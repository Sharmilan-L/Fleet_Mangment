"""
Simulation Control API Router per docs/simulation-requirements.md.
"""

import uuid

from fastapi import APIRouter, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from evolvex.simulator.runner import SimulationRunner
from evolvex.simulator.scenarios import ScenarioGenerator

router = APIRouter(prefix="/api/v1/simulator", tags=["Deterministic Telemetry Simulator"])


class StartSimulationRequest(BaseModel):
    """Payload for starting simulation run."""

    trip_id: uuid.UUID = Field(..., alias="tripId")
    scenario_code: str = Field(default="PITCH_DEMO_REPLAY", alias="scenarioCode")
    packet_interval_ms: int = Field(default=1000, alias="packetIntervalMs")
    random_seed: int = Field(default=2026, alias="randomSeed")


@router.get("/scenarios")
async def list_simulation_scenarios() -> JSONResponse:
    """Return metadata of available deterministic scenarios."""
    scenarios = ScenarioGenerator.list_scenarios()
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={"success": True, "data": scenarios},
    )


@router.get("/status")
async def get_simulation_status() -> JSONResponse:
    """Return current status of simulation runner."""
    runner = SimulationRunner()
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={"success": True, "data": runner.get_status()},
    )


@router.post("/start")
async def start_simulation(payload: StartSimulationRequest) -> JSONResponse:
    """Start simulation run for specified trip and scenario."""
    runner = SimulationRunner()
    try:
        data = await runner.start(
            trip_id=str(payload.trip_id),
            scenario_code=payload.scenario_code,
            packet_interval_ms=payload.packet_interval_ms,
            random_seed=payload.random_seed,
        )
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"success": True, "data": data},
        )
    except ValueError as err:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"success": False, "error": {"code": "SIMULATION_ERROR", "message": str(err)}},
        )


@router.post("/pause")
async def pause_simulation() -> JSONResponse:
    """Pause currently running simulation."""
    runner = SimulationRunner()
    try:
        data = await runner.pause()
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"success": True, "data": data},
        )
    except ValueError as err:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"success": False, "error": {"code": "SIMULATION_ERROR", "message": str(err)}},
        )


@router.post("/resume")
async def resume_simulation() -> JSONResponse:
    """Resume paused simulation."""
    runner = SimulationRunner()
    try:
        data = await runner.resume()
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"success": True, "data": data},
        )
    except ValueError as err:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"success": False, "error": {"code": "SIMULATION_ERROR", "message": str(err)}},
        )


@router.post("/stop")
async def stop_simulation() -> JSONResponse:
    """Stop running or paused simulation."""
    runner = SimulationRunner()
    data = await runner.stop()
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={"success": True, "data": data},
    )
