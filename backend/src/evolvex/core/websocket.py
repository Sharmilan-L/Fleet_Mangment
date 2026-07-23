"""
Real-time WebSocket Connection Manager and Broadcaster.

Manages active WebSocket client connections per trip_id and broadcasts live telemetry snapshots,
detected events, score updates, and trip status changes per Milestone 7 requirements.
"""

from typing import Any

from fastapi import WebSocket

from evolvex.core.logging import logger


class ConnectionManager:
    """Manages active WebSocket connections grouped by trip_id."""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.active_connections = {}
        return cls._instance

    async def connect(self, websocket: WebSocket, trip_id: str) -> None:
        """Accept and register client connection for trip_id."""
        await websocket.accept()
        if trip_id not in self.active_connections:
            self.active_connections[trip_id] = []
        self.active_connections[trip_id].append(websocket)
        logger.info("WebSocket connected for trip: %s", trip_id)

    def disconnect(self, websocket: WebSocket, trip_id: str) -> None:
        """Unregister client connection."""
        if trip_id in self.active_connections:
            if websocket in self.active_connections[trip_id]:
                self.active_connections[trip_id].remove(websocket)
            if not self.active_connections[trip_id]:
                del self.active_connections[trip_id]
        logger.info("WebSocket disconnected for trip: %s", trip_id)

    async def broadcast_to_trip(
        self, trip_id: str, event_type: str, payload: dict[str, Any]
    ) -> None:
        """Broadcast JSON message to all active clients for a trip."""
        connections = self.active_connections.get(trip_id, [])
        if not connections:
            return

        message = {
            "type": event_type,
            "tripId": trip_id,
            "data": payload,
        }

        disconnected: list[WebSocket] = []
        for connection in connections:
            try:
                await connection.send_json(message)
            except Exception as err:
                logger.warning("Failed to send WebSocket message: %s", err)
                disconnected.append(connection)

        for conn in disconnected:
            self.disconnect(conn, trip_id)


manager = ConnectionManager()
