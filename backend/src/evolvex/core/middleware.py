import uuid
from collections.abc import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware


class RequestIDMiddleware(BaseHTTPMiddleware):
    """
    Middleware for Request Correlation.

    - Validates client-supplied X-Request-ID or generates a unique req_ UUID.
    - Stores the identifier in request.state.request_id.
    - Attaches X-Request-ID to the outgoing response headers.
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        header_request_id = request.headers.get("X-Request-ID")
        if header_request_id and header_request_id.strip():
            request_id = header_request_id.strip()
        else:
            request_id = f"req_{uuid.uuid4()}"

        request.state.request_id = request_id
        response: Response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response
