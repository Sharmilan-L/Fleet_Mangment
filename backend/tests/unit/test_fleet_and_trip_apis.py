"""
API integration tests for essential Fleet and Trip endpoints.
"""

import hashlib
import uuid
from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from evolvex.core.database import get_session_factory
from evolvex.db.models import (
    AssignmentStatus,
    Device,
    DeviceAdminStatus,
    DeviceAssignment,
    DeviceType,
    Driver,
    DriverStatus,
    Organization,
    OrganizationStatus,
    RuleSet,
    RuleSetVersion,
    RuleSetVersionStatus,
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
async def setup_fleet_db() -> dict:
    session_factory = get_session_factory()
    async with session_factory() as session:
        org = Organization(
            name="Fleet API Test Org",
            organization_code=f"ORG-FLT-{uuid.uuid4().hex[:6]}",
            status=OrganizationStatus.ACTIVE,
        )
        session.add(org)
        await session.flush()

        raw_key = "fleet-secret-key"
        device = Device(
            organization_id=org.id,
            device_code=f"DEV-FLT-{uuid.uuid4().hex[:6]}",
            display_name="Fleet Tracker",
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
            make="Nissan",
            model="Leaf",
            status=VehicleStatus.ACTIVE,
        )
        driver = Driver(
            organization_id=org.id,
            employee_code=f"EMP-{uuid.uuid4().hex[:6]}",
            first_name="Bob",
            last_name="Marley",
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

        rule_set = RuleSet(
            organization_id=org.id,
            name="Default Rule Set",
            status="ACTIVE",
        )
        session.add(rule_set)
        await session.flush()

        rule_version = RuleSetVersion(
            rule_set_id=rule_set.id,
            version_number=1,
            status=RuleSetVersionStatus.ACTIVE,
        )
        session.add(rule_version)
        await session.commit()

        return {
            "org": org,
            "device": device,
            "vehicle": vehicle,
            "driver": driver,
            "assignment": assignment,
            "rule_version": rule_version,
            "raw_key": raw_key,
        }


@pytest.mark.asyncio
async def test_list_fleet_resources(api_client: AsyncClient, setup_fleet_db: dict) -> None:
    resp_drivers = await api_client.get("/api/v1/drivers")
    assert resp_drivers.status_code == 200
    assert resp_drivers.json()["success"] is True

    resp_vehicles = await api_client.get("/api/v1/vehicles")
    assert resp_vehicles.status_code == 200
    assert resp_vehicles.json()["success"] is True

    resp_devices = await api_client.get("/api/v1/devices")
    assert resp_devices.status_code == 200
    assert resp_devices.json()["success"] is True

    resp_asgn = await api_client.get("/api/v1/device-assignments")
    assert resp_asgn.status_code == 200
    assert resp_asgn.json()["success"] is True


@pytest.mark.asyncio
async def test_trip_lifecycle_start_end_summary(
    api_client: AsyncClient, setup_fleet_db: dict
) -> None:
    driver = setup_fleet_db["driver"]
    vehicle = setup_fleet_db["vehicle"]

    # 1. Start Trip
    start_payload = {
        "driverId": str(driver.id),
        "vehicleId": str(vehicle.id),
        "tripMode": "TEST",
        "appliedSpeedLimitKmh": 70.0,
        "startReason": "Pitch Test",
    }
    resp_start = await api_client.post("/api/v1/trips", json=start_payload)
    assert resp_start.status_code == 201
    start_data = resp_start.json()["data"]
    trip_id = start_data["id"]
    assert start_data["status"] == "ACTIVE"
    assert start_data["tripMode"] == "TEST"

    # 2. Get Active Trips
    resp_active = await api_client.get("/api/v1/trips/active")
    assert resp_active.status_code == 200
    active_trips = resp_active.json()["data"]
    assert any(t["id"] == trip_id for t in active_trips)

    # 3. Get Live Snapshot
    resp_live = await api_client.get(f"/api/v1/trips/{trip_id}/live")
    assert resp_live.status_code == 200
    live_data = resp_live.json()["data"]
    assert live_data["trip"]["id"] == trip_id

    # 4. End Trip
    resp_end = await api_client.post(f"/api/v1/trips/{trip_id}/end", json={"endReason": "Finished"})
    assert resp_end.status_code == 200
    assert resp_end.json()["data"]["status"] == "COMPLETED"

    # 5. Get Summary
    resp_summary = await api_client.get(f"/api/v1/trips/{trip_id}/summary")
    assert resp_summary.status_code == 200
    summary_data = resp_summary.json()["data"]
    assert summary_data["tripId"] == trip_id
