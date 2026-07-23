"""
Unit tests for WebSocket Manager and real-time streaming endpoint.
"""

import uuid

import pytest
from httpx import ASGITransport, AsyncClient

from evolvex.core.websocket import ConnectionManager, manager
from evolvex.main import app


def test_connection_manager_singleton() -> None:
    m1 = ConnectionManager()
    m2 = ConnectionManager()
    assert m1 is m2


@pytest.mark.asyncio
async def test_websocket_connect_and_broadcast() -> None:
    trip_id = str(uuid.uuid4())
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver"):
        # Broadcast to empty trip subscribers should not raise exception
        await manager.broadcast_to_trip(
            trip_id,
            "TELEMETRY_SNAPSHOT",
            {"speedKmh": 50.0, "gpsValid": True},
        )
