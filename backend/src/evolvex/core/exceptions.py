from datetime import UTC, datetime
from typing import Any

from fastapi import Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from evolvex.core.logging import logger


def format_error_envelope(
    code: str,
    message: str,
    request_id: str,
    details: list[dict[str, Any]] | None = None,
    status_code: int = status.HTTP_400_BAD_REQUEST,
) -> JSONResponse:
    """
    Formats standard API error response envelope adhering to API Contract §10.
    """
    now_utc = datetime.now(UTC).isoformat()
    content = {
        "success": False,
        "error": {
            "code": code,
            "message": message,
        },
        "meta": {
            "requestId": request_id,
            "timestamp": now_utc,
        },
    }
    if details:
        content["error"]["details"] = details

    return JSONResponse(status_code=status_code, content=jsonable_encoder(content))


async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    request_id = getattr(request.state, "request_id", "req_unknown")
    code = getattr(exc, "code", "HTTP_ERROR")
    logger.warning(
        f"HTTP exception: status={exc.status_code} code={code} detail={exc.detail}",
        extra={"request_id": request_id},
    )
    return format_error_envelope(
        code=code if isinstance(code, str) else "HTTP_ERROR",
        message=str(exc.detail),
        request_id=request_id,
        status_code=exc.status_code,
    )


async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    request_id = getattr(request.state, "request_id", "req_unknown")
    details = []
    for err in exc.errors():
        loc_str = ".".join(str(item) for item in err.get("loc", []) if item != "body")
        details.append(
            {
                "field": loc_str or "request",
                "message": err.get("msg", "Validation error"),
            }
        )

    logger.warning(
        f"Validation error: {details}",
        extra={"request_id": request_id},
    )

    return format_error_envelope(
        code="VALIDATION_ERROR",
        message="Request payload or parameters failed validation",
        request_id=request_id,
        details=details,
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
    )


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    request_id = getattr(request.state, "request_id", "req_unknown")
    logger.error(
        f"Unhandled internal server error: {exc}",
        exc_info=exc,
        extra={"request_id": request_id},
    )
    return format_error_envelope(
        code="INTERNAL_SERVER_ERROR",
        message="An unexpected internal server error occurred",
        request_id=request_id,
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )
