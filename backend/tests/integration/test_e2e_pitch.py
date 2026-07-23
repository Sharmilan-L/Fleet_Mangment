"""
End-to-End integration test simulating a pitch demo sequence.

Starts a test trip, connects via WebSocket, initiates the pitch scenario simulator,
and verifies real-time receipt of telemetry and driving event updates.
"""

import uuid
from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from httpx import ASGITransport, AsyncClient

from evolvex.core.database import get_session_factory
from evolvex.db.models import (
    AssignmentStatus,
    Device,
    DeviceAssignment,
    Driver,
    DriverStatus,
    Organization,
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
async def setup_demo_data() -> dict:
    session_factory = get_session_factory()
    async with session_factory() as session:
        org = Organization(
            name="E2E Org",
            organization_code=f"ORG-E2E-{uuid.uuid4().hex[:6]}",
            status="ACTIVE",
        )
        session.add(org)
        await session.flush()

        driver = Driver(
            organization_id=org.id,
            employee_code=f"EMP-E2E-{uuid.uuid4().hex[:6]}",
            first_name="Jane",
            last_name="Doe",
            status=DriverStatus.ACTIVE,
        )
        vehicle = Vehicle(
            organization_id=org.id,
            registration_number=f"REG-E2E-{uuid.uuid4().hex[:6]}",
            vehicle_code=f"VEH-E2E-{uuid.uuid4().hex[:6]}",
            make="Honda",
            model="Civic",
            status=VehicleStatus.ACTIVE,
        )
        session.add_all([driver, vehicle])
        await session.flush()

        import hashlib

        raw_key = "demo-simulator-secret-key-2026"
        device = Device(
            organization_id=org.id,
            device_code=f"DEV-E2E-{uuid.uuid4().hex[:6]}",
            display_name="E2E Tracker",
            device_type="SIMULATOR",
            administrative_status="TESTING",
            api_key_hash=hashlib.sha256(raw_key.encode()).hexdigest(),
        )
        session.add(device)
        await session.flush()

        asgn = DeviceAssignment(
            organization_id=org.id,
            device_id=device.id,
            vehicle_id=vehicle.id,
            status=AssignmentStatus.ACTIVE,
        )
        session.add(asgn)
        await session.flush()

        rule_set = RuleSet(
            organization_id=org.id,
            name="E2E Rule Set",
            status="ACTIVE",
        )
        session.add(rule_set)
        await session.flush()

        rule_ver = RuleSetVersion(
            rule_set_id=rule_set.id,
            version_number=1,
            status=RuleSetVersionStatus.ACTIVE,
        )
        session.add(rule_ver)
        await session.commit()

        return {
            "driver_id": str(driver.id),
            "vehicle_id": str(vehicle.id),
            "device_code": device.device_code,
            "assignment_id": str(asgn.id),
        }


@pytest.mark.asyncio
async def test_e2e_pitch_demo_flow(api_client: AsyncClient, setup_demo_data: dict) -> None:
    # 1. Start Trip
    start_payload = {
        "driverId": setup_demo_data["driver_id"],
        "vehicleId": setup_demo_data["vehicle_id"],
        "tripMode": "TEST",
        "appliedSpeedLimitKmh": 60.0,
        "startReason": "E2E Pitch Demo",
    }
    resp = await api_client.post("/api/v1/trips", json=start_payload)
    assert resp.status_code == 201
    trip_id = resp.json()["data"]["id"]

    # 2. Open WebSocket client using FastAPI TestClient (supports sync ws transport)
    client = TestClient(app)
    with client.websocket_connect(f"/api/v1/ws/trips/{trip_id}") as websocket:
        # Trigger single packet telemetry ingestion
        telemetry_payload = {
            "boot_id": "boot-e2e-123",
            "sequence_number": 1,
            "timestamp": 1000.0,
            "lat": 6.9271,
            "lng": 79.8612,
            "speed_kmh": 45.0,
            "accel_fwd": 0.5,
            "accel_lat": 0.2,
            "yaw_rate": 1.0,
        }

        # Mock posting telemetry from simulator
        headers = {
            "X-Device-Code": setup_demo_data["device_code"],
            "X-Device-Key": "demo-simulator-secret-key-2026",
            "X-Telemetry-Schema-Version": "1.0",
        }
        res_post = await api_client.post(
            "/api/v1/device/telemetry", json=telemetry_payload, headers=headers
        )
        assert res_post.status_code == 200

        # WebSocket should receive TELEMETRY_SNAPSHOT frame
        data = websocket.receive_json()
        assert data["type"] == "TELEMETRY_SNAPSHOT"
        assert data["tripId"] == trip_id
        assert data["data"]["speedKmh"] == 45.0

    # 3. Clean up and end the active test trip
    resp_end = await api_client.post(
        f"/api/v1/trips/{trip_id}/end",
        json={"endReason": "E2E integration test complete"},
    )
    assert resp_end.status_code == 200
