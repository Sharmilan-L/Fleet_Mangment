"""
API Integration tests for POST /api/v1/device/telemetry endpoint.
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
    Trip,
    TripMode,
    TripStatus,
    Vehicle,
    VehicleStatus,
)
from evolvex.main import app


@pytest_asyncio.fixture
async def api_client() -> AsyncGenerator[AsyncClient, None]:
    """Async TestClient for FastAPI app."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://testserver"
    ) as client:
        yield client


@pytest_asyncio.fixture
async def setup_telemetry_db() -> dict:
    """Setup organization, user, driver, vehicle, device, assignment, and trip in DB."""
    session_factory = get_session_factory()
    async with session_factory() as db_session:
        org = Organization(
            name="Telemetry Test Fleet",
            organization_code=f"ORG-TEL-{uuid.uuid4().hex[:6]}",
            status=OrganizationStatus.ACTIVE,
        )
        db_session.add(org)
        await db_session.flush()

        raw_key = "secret-test-key-123"
        hashed_key = hashlib.sha256(raw_key.encode()).hexdigest()

        device = Device(
            organization_id=org.id,
            device_code=f"DEV-TEL-{uuid.uuid4().hex[:6]}",
            display_name="Test Hardware Tracker",
            device_type=DeviceType.HARDWARE,
            administrative_status=DeviceAdminStatus.ACTIVE,
            api_key_hash=hashed_key,
        )
        disabled_device = Device(
            organization_id=org.id,
            device_code=f"DEV-DIS-{uuid.uuid4().hex[:6]}",
            display_name="Disabled Tracker",
            device_type=DeviceType.HARDWARE,
            administrative_status=DeviceAdminStatus.DISABLED,
            api_key_hash=hashed_key,
        )
        db_session.add_all([device, disabled_device])
        await db_session.flush()

        vehicle = Vehicle(
            organization_id=org.id,
            registration_number=f"REG-{uuid.uuid4().hex[:6]}",
            vehicle_code=f"VEH-{uuid.uuid4().hex[:6]}",
            make="Toyota",
            model="Hilux",
            status=VehicleStatus.ACTIVE,
        )
        driver = Driver(
            organization_id=org.id,
            employee_code=f"EMP-{uuid.uuid4().hex[:6]}",
            first_name="Jane",
            last_name="Doe",
            status=DriverStatus.ACTIVE,
        )
        db_session.add_all([vehicle, driver])
        await db_session.flush()

        assignment = DeviceAssignment(
            organization_id=org.id,
            device_id=device.id,
            vehicle_id=vehicle.id,
            status=AssignmentStatus.ACTIVE,
        )
        db_session.add(assignment)
        await db_session.flush()

        trip = Trip(
            organization_id=org.id,
            trip_code=f"TRIP-{uuid.uuid4().hex[:6]}",
            driver_id=driver.id,
            device_assignment_id=assignment.id,
            trip_mode=TripMode.OFFICIAL,
            status=TripStatus.ACTIVE,
        )
        db_session.add(trip)
        await db_session.commit()

        return {
            "org": org,
            "device": device,
            "disabled_device": disabled_device,
            "vehicle": vehicle,
            "driver": driver,
            "assignment": assignment,
            "trip": trip,
            "raw_key": raw_key,
        }


@pytest.mark.asyncio
async def test_valid_hardware_telemetry_packet(
    api_client: AsyncClient, setup_telemetry_db: dict
) -> None:
    """Test successful telemetry submission with full GPS, active assignment, and active trip."""
    device = setup_telemetry_db["device"]
    raw_key = setup_telemetry_db["raw_key"]
    trip = setup_telemetry_db["trip"]

    headers = {
        "X-Device-Code": device.device_code,
        "X-Device-Key": raw_key,
        "X-Telemetry-Schema-Version": "1.0",
    }
    payload = {
        "boot_id": "boot-test-001",
        "sequence_number": 100,
        "timestamp": 1721732160,
        "lat": 7.2906,
        "lng": 80.6337,
        "speed_kmh": 55.0,
        "accel_fwd": 0.5,
        "accel_lat": 0.1,
        "yaw_rate": 1.2,
    }

    response = await api_client.post("/api/v1/device/telemetry", json=payload, headers=headers)
    assert response.status_code == 200
    res_json = response.json()
    assert res_json["success"] is True
    assert res_json["data"]["status"] == "ACCEPTED"
    assert res_json["data"]["processingStatus"] == "PROCESSED"
    assert "telemetryId" in res_json["data"]
    assert res_json["data"]["tripId"] == str(trip.id)


@pytest.mark.asyncio
async def test_duplicate_telemetry_packet(
    api_client: AsyncClient, setup_telemetry_db: dict
) -> None:
    """Test packet idempotency returning DUPLICATE for repeated (boot_id, sequence_number)."""
    device = setup_telemetry_db["device"]
    raw_key = setup_telemetry_db["raw_key"]

    headers = {
        "X-Device-Code": device.device_code,
        "X-Device-Key": raw_key,
    }
    payload = {
        "boot_id": "boot-test-dup",
        "sequence_number": 500,
        "speed_kmh": 40.0,
        "accel_fwd": 0.0,
        "accel_lat": 0.0,
        "yaw_rate": 0.0,
    }

    # First send -> ACCEPTED
    resp1 = await api_client.post("/api/v1/device/telemetry", json=payload, headers=headers)
    assert resp1.status_code == 200
    res1 = resp1.json()
    first_id = res1["data"]["telemetryId"]

    # Second send -> DUPLICATE
    resp2 = await api_client.post("/api/v1/device/telemetry", json=payload, headers=headers)
    assert resp2.status_code == 200
    res2 = resp2.json()
    assert res2["success"] is True
    assert res2["data"]["status"] == "DUPLICATE"
    assert res2["data"]["processingStatus"] == "DUPLICATE"
    assert res2["data"]["telemetryId"] == first_id


@pytest.mark.asyncio
async def test_invalid_api_key(api_client: AsyncClient, setup_telemetry_db: dict) -> None:
    """Test rejecting invalid X-Device-Key with 401 AUTHENTICATION_FAILED."""
    device = setup_telemetry_db["device"]

    headers = {
        "X-Device-Code": device.device_code,
        "X-Device-Key": "wrong-secret-key",
    }
    payload = {
        "boot_id": "boot-test-auth",
        "sequence_number": 1,
        "speed_kmh": 10.0,
        "accel_fwd": 0.0,
        "accel_lat": 0.0,
        "yaw_rate": 0.0,
    }

    response = await api_client.post("/api/v1/device/telemetry", json=payload, headers=headers)
    assert response.status_code == 401
    res_json = response.json()
    assert res_json["success"] is False
    assert res_json["error"]["code"] == "AUTHENTICATION_FAILED"


@pytest.mark.asyncio
async def test_disabled_device(api_client: AsyncClient, setup_telemetry_db: dict) -> None:
    """Test rejecting disabled device with 401 AUTHENTICATION_FAILED."""
    disabled_device = setup_telemetry_db["disabled_device"]
    raw_key = setup_telemetry_db["raw_key"]

    headers = {
        "X-Device-Code": disabled_device.device_code,
        "X-Device-Key": raw_key,
    }
    payload = {
        "boot_id": "boot-disabled",
        "sequence_number": 1,
        "speed_kmh": 10.0,
        "accel_fwd": 0.0,
        "accel_lat": 0.0,
        "yaw_rate": 0.0,
    }

    response = await api_client.post("/api/v1/device/telemetry", json=payload, headers=headers)
    assert response.status_code == 401
    res_json = response.json()
    assert res_json["success"] is False
    assert res_json["error"]["code"] == "AUTHENTICATION_FAILED"


@pytest.mark.asyncio
async def test_no_active_assignment_or_trip(api_client: AsyncClient) -> None:
    """Test telemetry ingestion for an unassigned standalone device."""
    session_factory = get_session_factory()
    async with session_factory() as db_session:
        org = Organization(
            name="Standalone Fleet",
            organization_code=f"ORG-SA-{uuid.uuid4().hex[:6]}",
            status=OrganizationStatus.ACTIVE,
        )
        db_session.add(org)
        await db_session.flush()

        raw_key = "standalone-key"
        hashed_key = hashlib.sha256(raw_key.encode()).hexdigest()

        standalone_device = Device(
            organization_id=org.id,
            device_code=f"DEV-SA-{uuid.uuid4().hex[:6]}",
            display_name="Unassigned Tracker",
            device_type=DeviceType.HARDWARE,
            administrative_status=DeviceAdminStatus.ACTIVE,
            api_key_hash=hashed_key,
        )
        db_session.add(standalone_device)
        await db_session.commit()

    headers = {
        "X-Device-Code": standalone_device.device_code,
        "X-Device-Key": raw_key,
    }
    payload = {
        "boot_id": "boot-unassigned",
        "sequence_number": 1,
        "lat": 6.9271,
        "lng": 79.8612,
        "speed_kmh": 30.0,
        "accel_fwd": 0.1,
        "accel_lat": 0.0,
        "yaw_rate": 0.0,
    }

    response = await api_client.post("/api/v1/device/telemetry", json=payload, headers=headers)
    assert response.status_code == 200
    res_json = response.json()
    assert res_json["success"] is True
    assert res_json["data"]["status"] == "ACCEPTED"
    assert res_json["data"]["processingStatus"] == "PROCESSED"
    assert "tripId" not in res_json["data"]


@pytest.mark.asyncio
async def test_missing_gps_partial_telemetry(
    api_client: AsyncClient, setup_telemetry_db: dict
) -> None:
    """Test telemetry accepted with PARTIAL status and warning when GPS is unavailable."""
    device = setup_telemetry_db["device"]
    raw_key = setup_telemetry_db["raw_key"]

    headers = {
        "X-Device-Code": device.device_code,
        "X-Device-Key": raw_key,
    }
    payload = {
        "boot_id": "boot-no-gps",
        "sequence_number": 99,
        "lat": None,
        "lng": None,
        "speed_kmh": 45.0,
        "accel_fwd": -0.2,
        "accel_lat": 0.0,
        "yaw_rate": 0.5,
    }

    response = await api_client.post("/api/v1/device/telemetry", json=payload, headers=headers)
    assert response.status_code == 200
    res_json = response.json()
    assert res_json["success"] is True
    assert res_json["data"]["status"] == "ACCEPTED"
    assert res_json["data"]["processingStatus"] == "PARTIAL"
    assert "warnings" in res_json["data"]
    assert res_json["data"]["warnings"][0]["code"] == "GPS_UNAVAILABLE"


@pytest.mark.asyncio
async def test_extreme_sensor_values_validation(
    api_client: AsyncClient, setup_telemetry_db: dict
) -> None:
    """Test rejecting extreme out-of-range sensor values (speed > 250 km/h) with 400."""
    device = setup_telemetry_db["device"]
    raw_key = setup_telemetry_db["raw_key"]

    headers = {
        "X-Device-Code": device.device_code,
        "X-Device-Key": raw_key,
    }
    payload = {
        "boot_id": "boot-extreme",
        "sequence_number": 1,
        "speed_kmh": 350.0,  # Extreme invalid speed
        "accel_fwd": 0.0,
        "accel_lat": 0.0,
        "yaw_rate": 0.0,
    }

    response = await api_client.post("/api/v1/device/telemetry", json=payload, headers=headers)
    assert response.status_code == 400
    res_json = response.json()
    assert res_json["success"] is False
    assert res_json["error"]["code"] == "TELEMETRY_VALIDATION_FAILED"
    assert res_json["error"]["details"][0]["field"] == "speed_kmh"


@pytest.mark.asyncio
async def test_valid_simulator_packet(
    api_client: AsyncClient, setup_telemetry_db: dict
) -> None:
    """Test telemetry submission for a simulator device."""
    session_factory = get_session_factory()
    async with session_factory() as db_session:
        org = setup_telemetry_db["org"]
        raw_key = "sim-key-999"
        sim_device = Device(
            organization_id=org.id,
            device_code=f"DEV-SIM-{uuid.uuid4().hex[:6]}",
            display_name="Simulator Tracker",
            device_type=DeviceType.SIMULATOR,
            administrative_status=DeviceAdminStatus.TESTING,
            api_key_hash=hashlib.sha256(raw_key.encode()).hexdigest(),
        )
        db_session.add(sim_device)
        await db_session.commit()

    headers = {
        "X-Device-Code": sim_device.device_code,
        "X-Device-Key": raw_key,
    }
    payload = {
        "boot_id": "boot-sim-001",
        "sequence_number": 1,
        "lat": 6.9271,
        "lng": 79.8612,
        "speed_kmh": 60.0,
        "accel_fwd": 0.2,
        "accel_lat": 0.0,
        "yaw_rate": 0.0,
    }
    response = await api_client.post("/api/v1/device/telemetry", json=payload, headers=headers)
    assert response.status_code == 200
    res_json = response.json()
    assert res_json["success"] is True
    assert res_json["data"]["status"] == "ACCEPTED"


@pytest.mark.asyncio
async def test_invalid_coordinates(
    api_client: AsyncClient, setup_telemetry_db: dict
) -> None:
    """Test telemetry submission with out of bounds latitude (> 90.0)."""
    device = setup_telemetry_db["device"]
    raw_key = setup_telemetry_db["raw_key"]
    headers = {
        "X-Device-Code": device.device_code,
        "X-Device-Key": raw_key,
    }
    payload = {
        "boot_id": "boot-invalid-coord",
        "sequence_number": 1,
        "lat": 120.0,  # Invalid latitude
        "lng": 80.0,
        "speed_kmh": 40.0,
        "accel_fwd": 0.0,
        "accel_lat": 0.0,
        "yaw_rate": 0.0,
    }
    response = await api_client.post("/api/v1/device/telemetry", json=payload, headers=headers)
    assert response.status_code == 200
    res_json = response.json()
    assert res_json["success"] is True
    assert res_json["data"]["processingStatus"] == "PARTIAL"


@pytest.mark.asyncio
async def test_unsupported_schema_version(
    api_client: AsyncClient, setup_telemetry_db: dict
) -> None:
    """Test rejecting unsupported telemetry schema version (e.g. 2.0)."""
    device = setup_telemetry_db["device"]
    raw_key = setup_telemetry_db["raw_key"]
    headers = {
        "X-Device-Code": device.device_code,
        "X-Device-Key": raw_key,
        "X-Telemetry-Schema-Version": "2.0",
    }
    payload = {
        "boot_id": "boot-v2",
        "sequence_number": 1,
        "speed_kmh": 40.0,
        "accel_fwd": 0.0,
        "accel_lat": 0.0,
        "yaw_rate": 0.0,
    }
    response = await api_client.post("/api/v1/device/telemetry", json=payload, headers=headers)
    assert response.status_code == 400
    res_json = response.json()
    assert res_json["error"]["code"] == "UNSUPPORTED_SCHEMA_VERSION"

