"""
WebSocket API Endpoint for Real-time Trip Streaming.
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from evolvex.core.websocket import manager

router = APIRouter(prefix="/api/v1/ws", tags=["Real-Time Streaming"])


@router.websocket("/trips/{trip_id}")
async def websocket_trip_endpoint(websocket: WebSocket, trip_id: str) -> None:
    """WebSocket endpoint streaming live telemetry, events, and score changes for a trip."""
    await manager.connect(websocket, trip_id)
    try:
        while True:
            # Keep connection open and receive optional client heartbeats / messages
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket, trip_id)
    except Exception:
        manager.disconnect(websocket, trip_id)
