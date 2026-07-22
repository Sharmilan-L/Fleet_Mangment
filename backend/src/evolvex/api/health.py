from datetime import UTC, datetime

from fastapi import APIRouter, Request, status
from fastapi.responses import JSONResponse

from evolvex.core.database import ping_database
from evolvex.core.exceptions import format_error_envelope
from evolvex.core.logging import logger

router = APIRouter()


@router.get("/health", status_code=status.HTTP_200_OK)
async def get_process_liveness() -> dict[str, str]:
    """
    Process Liveness Endpoint (API Contract §16).
    Confirms FastAPI ASGI server is running.
    """
    now_utc = datetime.now(UTC).isoformat()
    return {
        "status": "healthy",
        "service": "evolvex-api",
        "timestamp": now_utc,
    }


@router.get("/api/v1/health/database")
async def get_database_readiness(request: Request) -> JSONResponse:
    """
    Database Readiness Endpoint (API Contract §17).
    Executes SELECT 1 query against PostgreSQL database.
    """
    request_id = getattr(request.state, "request_id", "req_unknown")
    now_utc = datetime.now(UTC).isoformat()

    try:
        is_connected = await ping_database()
        if not is_connected:
            raise ConnectionError("Database ping returned false")

        content = {
            "success": True,
            "data": {
                "status": "healthy",
                "database": "connected",
            },
            "meta": {
                "requestId": request_id,
                "timestamp": now_utc,
            },
        }
        return JSONResponse(status_code=status.HTTP_200_OK, content=content)

    except Exception as exc:
        logger.warning(
            f"Database readiness check failed: {exc}",
            extra={"request_id": request_id},
        )
        return format_error_envelope(
            code="DATABASE_UNAVAILABLE",
            message="Database connectivity check failed",
            request_id=request_id,
            details=[
                {
                    "field": "database",
                    "message": "Could not establish connection to PostgreSQL",
                }
            ],
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        )
