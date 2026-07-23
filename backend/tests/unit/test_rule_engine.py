"""
Unit & Integration tests for Rule Engine and Driving Event Detection.
"""

import hashlib
import uuid
from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select

from evolvex.core.database import get_session_factory
from evolvex.db.models import (
    AssignmentStatus,
    Device,
    DeviceAdminStatus,
    DeviceAssignment,
    DeviceType,
    Driver,
    DriverStatus,
    DrivingEvent,
    EventType,
    Organization,
    OrganizationStatus,
    Trip,
    TripMode,
    TripScoreLedger,
    TripScoreState,
    TripStatus,
    Vehicle,
    VehicleStatus,
)
from evolvex.main import app


@pytest_asyncio.fixture
async def api_client() -> AsyncGenerator[AsyncClient, None]:
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://testserver"
    ) as client:
        yield client


@pytest_asyncio.fixture
async def setup_engine_db() -> dict:
    session_factory = get_session_factory()
    async with session_factory() as session:
        org = Organization(
            name="Engine Test Org",
            organization_code=f"ORG-ENG-{uuid.uuid4().hex[:6]}",
            status=OrganizationStatus.ACTIVE,
        )
        session.add(org)
        await session.flush()

        raw_key = "rule-secret-key"
        device = Device(
            organization_id=org.id,
            device_code=f"DEV-ENG-{uuid.uuid4().hex[:6]}",
            display_name="Engine Tracker",
            device_type=DeviceType.HARDWARE,
            administrative_status=DeviceAdminStatus.ACTIVE,
            api_key_hash=hashlib.sha256(raw_key.encode()).hexdigest(),
        )
        session.add(device)
        await session.flush()

        vehicle = Vehicle(
            organization_id=org.id,
            registration_number=f"REG-{uuid.uuid4().hex[:6]}",
            vehicle_code=f"VEH-{uuid.uuid4().hex[:6]}",
            make="Toyota",
            model="Camry",
            status=VehicleStatus.ACTIVE,
        )
        driver = Driver(
            organization_id=org.id,
            employee_code=f"EMP-{uuid.uuid4().hex[:6]}",
            first_name="Alice",
            last_name="Smith",
            status=DriverStatus.ACTIVE,
        )
        session.add_all([vehicle, driver])
        await session.flush()

        assignment = DeviceAssignment(
            organization_id=org.id,
            device_id=device.id,
            vehicle_id=vehicle.id,
            status=AssignmentStatus.ACTIVE,
        )
        session.add(assignment)
        await session.flush()

        trip = Trip(
            organization_id=org.id,
            trip_code=f"TRIP-ENG-{uuid.uuid4().hex[:6]}",
            driver_id=driver.id,
            device_assignment_id=assignment.id,
            trip_mode=TripMode.OFFICIAL,
            status=TripStatus.ACTIVE,
            applied_speed_limit_kmh=60.0,
        )
        session.add(trip)
        await session.commit()

        return {
            "org": org,
            "device": device,
            "assignment": assignment,
            "trip": trip,
            "raw_key": raw_key,
        }


@pytest.mark.asyncio
async def test_harsh_braking_detection_and_score_deduction(
    api_client: AsyncClient, setup_engine_db: dict
) -> None:
    device = setup_engine_db["device"]
    raw_key = setup_engine_db["raw_key"]
    trip = setup_engine_db["trip"]

    headers = {
        "X-Device-Code": device.device_code,
        "X-Device-Key": raw_key,
    }

    boot_id = f"boot-hb-{uuid.uuid4().hex[:6]}"

    base_ts = 1721732160.0

    # Send packet 1 (candidate start)
    p1 = {
        "boot_id": boot_id,
        "sequence_number": 1,
        "timestamp": base_ts,
        "lat": 6.9271,
        "lng": 79.8612,
        "speed_kmh": 50.0,
        "accel_fwd": -4.0,  # Negative accel (harsh braking candidate)
        "accel_lat": 0.0,
        "yaw_rate": 0.0,
    }
    resp1 = await api_client.post("/api/v1/device/telemetry", json=p1, headers=headers)
    assert resp1.status_code == 200

    # Send packet 2 (sustained harsh braking after 1000ms -> confirms event!)
    p2 = {
        "boot_id": boot_id,
        "sequence_number": 2,
        "timestamp": base_ts + 1.0,
        "lat": 6.9272,
        "lng": 79.8613,
        "speed_kmh": 40.0,
        "accel_fwd": -4.5,
        "accel_lat": 0.0,
        "yaw_rate": 0.0,
    }
    resp2 = await api_client.post("/api/v1/device/telemetry", json=p2, headers=headers)
    assert resp2.status_code == 200

    # Check DB for created DrivingEvent and score deduction
    session_factory = get_session_factory()
    async with session_factory() as session:
        ev_stmt = select(DrivingEvent).where(
            DrivingEvent.trip_id == trip.id,
            DrivingEvent.event_type == EventType.HARSH_BRAKING,
        )
        ev_res = await session.execute(ev_stmt)
        events = ev_res.scalars().all()
        assert len(events) == 1
        assert events[0].primary_measurement == 4.5

        # Check score state
        sc_stmt = select(TripScoreState).where(TripScoreState.trip_id == trip.id)
        sc_res = await session.execute(sc_stmt)
        score_state = sc_res.scalar_one_or_none()
        assert score_state is not None
        assert score_state.current_score == 96.0  # 100.0 - 4.0 penalty

        # Check ledger entry
        lg_stmt = select(TripScoreLedger).where(
            TripScoreLedger.trip_id == trip.id,
            TripScoreLedger.source_event_id == events[0].id,
        )
        lg_res = await session.execute(lg_stmt)
        ledger_entry = lg_res.scalar_one_or_none()
        assert ledger_entry is not None
        assert ledger_entry.points_delta == -4.0
        assert ledger_entry.new_score == 96.0


@pytest.mark.asyncio
async def test_overspeeding_detection_and_score_deduction(
    api_client: AsyncClient, setup_engine_db: dict
) -> None:
    device = setup_engine_db["device"]
    raw_key = setup_engine_db["raw_key"]
    trip = setup_engine_db["trip"]

    headers = {
        "X-Device-Code": device.device_code,
        "X-Device-Key": raw_key,
    }

    boot_id = f"boot-os-{uuid.uuid4().hex[:6]}"
    base_ts = 1721732160.0

    # Send candidate overspeed packet (> 65.0 km/h)
    p1 = {
        "boot_id": boot_id,
        "sequence_number": 1,
        "timestamp": base_ts,
        "lat": 6.9271,
        "lng": 79.8612,
        "speed_kmh": 85.0,  # 25 km/h over limit
        "accel_fwd": 0.0,
        "accel_lat": 0.0,
        "yaw_rate": 0.0,
    }
    await api_client.post("/api/v1/device/telemetry", json=p1, headers=headers)

    # Sustained overspeed > 3000ms (4.0s later)
    p2 = {
        "boot_id": boot_id,
        "sequence_number": 2,
        "timestamp": base_ts + 4.0,
        "lat": 6.9273,
        "lng": 79.8614,
        "speed_kmh": 88.0,
        "accel_fwd": 0.0,
        "accel_lat": 0.0,
        "yaw_rate": 0.0,
    }
    await api_client.post("/api/v1/device/telemetry", json=p2, headers=headers)

    session_factory = get_session_factory()
    async with session_factory() as session:
        ev_stmt = select(DrivingEvent).where(
            DrivingEvent.trip_id == trip.id,
            DrivingEvent.event_type == EventType.OVERSPEEDING,
        )
        ev_res = await session.execute(ev_stmt)
        events = ev_res.scalars().all()
        assert len(events) == 1
        assert events[0].event_type == EventType.OVERSPEEDING
