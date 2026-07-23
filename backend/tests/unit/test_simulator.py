"""
Unit tests for Deterministic Telemetry Simulator and API endpoints.
"""

import uuid
from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from evolvex.main import app
from evolvex.simulator.scenarios import ScenarioGenerator


@pytest_asyncio.fixture
async def api_client() -> AsyncGenerator[AsyncClient, None]:
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://testserver"
    ) as client:
        yield client


def test_scenario_generator_list() -> None:
    scenarios = ScenarioGenerator.list_scenarios()
    assert len(scenarios) == 6
    codes = [s["code"] for s in scenarios]
    assert "NORMAL_CITY_DRIVING" in codes
    assert "HARSH_BRAKING_EVENT" in codes
    assert "SUDDEN_ACCELERATION_EVENT" in codes
    assert "OVERSPEEDING_SUSTAINED" in codes
    assert "SHARP_TURNING_EVENT" in codes
    assert "PITCH_DEMO_REPLAY" in codes


def test_deterministic_packet_generation() -> None:
    boot_id = "test-boot-1"
    p1 = ScenarioGenerator.generate_packets("HARSH_BRAKING_EVENT", boot_id, seed=2026)
    p2 = ScenarioGenerator.generate_packets("HARSH_BRAKING_EVENT", boot_id, seed=2026)
    assert len(p1) == len(p2)
    assert p1[0]["speed_kmh"] == p2[0]["speed_kmh"]
    assert p1[3]["accel_fwd"] == p2[3]["accel_fwd"]


@pytest.mark.asyncio
async def test_simulator_api_endpoints(api_client: AsyncClient) -> None:
    # List scenarios
    res_scenarios = await api_client.get("/api/v1/simulator/scenarios")
    assert res_scenarios.status_code == 200
    assert res_scenarios.json()["success"] is True

    # Status initial
    res_status = await api_client.get("/api/v1/simulator/status")
    assert res_status.status_code == 200
    assert res_status.json()["data"]["status"] == "STOPPED"

    # Start simulation
    trip_id = str(uuid.uuid4())
    res_start = await api_client.post(
        "/api/v1/simulator/start",
        json={"tripId": trip_id, "scenarioCode": "NORMAL_CITY_DRIVING", "packetIntervalMs": 5000},
    )
    assert res_start.status_code == 200
    assert res_start.json()["data"]["status"] == "RUNNING"

    # Pause
    res_pause = await api_client.post("/api/v1/simulator/pause")
    assert res_pause.status_code == 200
    assert res_pause.json()["data"]["status"] == "PAUSED"

    # Resume
    res_resume = await api_client.post("/api/v1/simulator/resume")
    assert res_resume.status_code == 200
    assert res_resume.json()["data"]["status"] == "RUNNING"

    # Stop
    res_stop = await api_client.post("/api/v1/simulator/stop")
    assert res_stop.status_code == 200
    assert res_stop.json()["data"]["status"] == "STOPPED"
