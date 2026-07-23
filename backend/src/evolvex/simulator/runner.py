"""
EvolveX Simulation Runner Service.

Manages simulation states (STOPPED, RUNNING, PAUSED, COMPLETED, FAILED)
and asynchronously posts generated telemetry packets to the backend API endpoint.
"""

import asyncio
import os
import uuid
from typing import Any

import httpx

from evolvex.core.logging import logger
from evolvex.simulator.scenarios import ScenarioGenerator


class SimulationRunner:
    """Singleton simulation runner service."""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._init_state()
        return cls._instance

    def _init_state(self) -> None:
        self.status: str = "STOPPED"
        self.trip_id: str | None = None
        self.scenario_code: str | None = None
        self.packet_interval_ms: int = 1000
        self.random_seed: int = 2026
        self.device_code: str = os.getenv("SIMULATOR_DEVICE_CODE", "SIM-DEVICE-001")
        self.device_key: str = os.getenv("SIMULATOR_DEVICE_KEY", "demo-simulator-secret-key-2026")
        self.api_url: str = os.getenv(
            "TELEMETRY_API_URL", "http://localhost:8000/api/v1/device/telemetry"
        )

        self.current_seq: int = 0
        self.total_packets: int = 0
        self.packets_sent: int = 0
        self.packets_failed: int = 0

        self._task: asyncio.Task | None = None
        self._pause_event: asyncio.Event = asyncio.Event()
        self._pause_event.set()

    def get_status(self) -> dict[str, Any]:
        """Return current status dictionary."""
        pct = (
            round((self.packets_sent / self.total_packets) * 100.0, 1)
            if self.total_packets > 0
            else 0.0
        )
        return {
            "status": self.status,
            "tripId": self.trip_id,
            "scenarioCode": self.scenario_code,
            "packetIntervalMs": self.packet_interval_ms,
            "packetsSent": self.packets_sent,
            "totalPackets": self.total_packets,
            "progressPercent": pct,
            "deviceCode": self.device_code,
        }

    async def start(
        self,
        trip_id: str,
        scenario_code: str,
        packet_interval_ms: int = 1000,
        random_seed: int = 2026,
    ) -> dict[str, Any]:
        """Start a new simulation run."""
        if self.status in ("RUNNING", "PAUSED"):
            raise ValueError(f"Simulation is already in {self.status} state.")

        if scenario_code not in ScenarioGenerator.SCENARIOS:
            raise ValueError(f"Unknown scenario code: {scenario_code}")

        # Resolve device assignment from Trip ID
        from evolvex.core.database import get_session_factory
        from evolvex.db.models import Trip, DeviceAssignment, Device
        from sqlalchemy.orm import selectinload
        from sqlalchemy import select

        session_factory = get_session_factory()
        async with session_factory() as session:
            stmt = (
                select(Trip)
                .options(
                    selectinload(Trip.device_assignment).selectinload(DeviceAssignment.device)
                )
                .where(Trip.id == uuid.UUID(trip_id))
            )
            res = await session.execute(stmt)
            trip = res.scalar_one_or_none()
            if trip and trip.device_assignment and trip.device_assignment.device:
                self.device_code = trip.device_assignment.device.device_code
                self.device_key = "demo-simulator-secret-key-2026"
                logger.info(
                    "Resolved simulation device code: %s for trip: %s",
                    self.device_code,
                    trip_id,
                )
            else:
                logger.warning(
                    "Could not resolve device code for trip_id: %s. Using default: %s",
                    trip_id,
                    self.device_code,
                )

        self.trip_id = trip_id
        self.scenario_code = scenario_code
        self.packet_interval_ms = max(250, min(5000, packet_interval_ms))
        self.random_seed = random_seed
        self.status = "RUNNING"
        self.packets_sent = 0
        self.packets_failed = 0

        self._pause_event.set()
        self._task = asyncio.create_task(self._run_loop())
        logger.info("Started simulation run for scenario: %s, trip: %s", scenario_code, trip_id)

        return self.get_status()

    async def pause(self) -> dict[str, Any]:
        """Pause running simulation."""
        if self.status != "RUNNING":
            raise ValueError(f"Cannot pause simulation in status: {self.status}")

        self.status = "PAUSED"
        self._pause_event.clear()
        logger.info("Paused simulation run for trip: %s", self.trip_id)
        return self.get_status()

    async def resume(self) -> dict[str, Any]:
        """Resume paused simulation."""
        if self.status != "PAUSED":
            raise ValueError(f"Cannot resume simulation in status: {self.status}")

        self.status = "RUNNING"
        self._pause_event.set()
        logger.info("Resumed simulation run for trip: %s", self.trip_id)
        return self.get_status()

    async def stop(self) -> dict[str, Any]:
        """Stop running simulation."""
        if self.status in ("STOPPED", "COMPLETED", "FAILED"):
            return self.get_status()

        self.status = "STOPPED"
        self._pause_event.set()
        if self._task and not self._task.done():
            self._task.cancel()

        logger.info("Stopped simulation run for trip: %s", self.trip_id)
        return self.get_status()

    async def _run_loop(self) -> None:
        """Internal asynchronous simulation dispatch loop."""
        try:
            boot_id = f"sim-run-{uuid.uuid4().hex[:8]}"
            packets = ScenarioGenerator.generate_packets(
                scenario_code=self.scenario_code,
                boot_id=boot_id,
                seed=self.random_seed,
            )
            self.total_packets = len(packets)

            async with httpx.AsyncClient(timeout=10.0) as client:
                for packet in packets:
                    await self._pause_event.wait()
                    if self.status != "RUNNING":
                        break

                    headers = {
                        "X-Device-Code": self.device_code,
                        "X-Device-Key": self.device_key,
                        "X-Telemetry-Schema-Version": "1.0",
                        "Content-Type": "application/json",
                    }

                    try:
                        resp = await client.post(self.api_url, json=packet, headers=headers)
                        if resp.status_code == 200:
                            self.packets_sent += 1
                        else:
                            self.packets_failed += 1
                            logger.warning(
                                "Telemetry POST returned status %d: %s",
                                resp.status_code,
                                resp.text,
                            )
                    except Exception as err:
                        self.packets_failed += 1
                        logger.error("Telemetry POST request failed: %s", err)

                    await asyncio.sleep(self.packet_interval_ms / 1000.0)

            if self.status == "RUNNING":
                self.status = "COMPLETED"
                logger.info("Completed simulation run for trip: %s", self.trip_id)

        except asyncio.CancelledError:
            self.status = "STOPPED"
        except Exception as exc:
            self.status = "FAILED"
            logger.error("Simulation run failed with error: %s", exc)
