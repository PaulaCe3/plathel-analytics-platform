"""Request correlation and safe access logging."""

import logging
import re
import time
from uuid import uuid4

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

from analytics_core.logging import bind_request_id, reset_request_id
from bi.api.error_handlers import unexpected_error_response

logger = logging.getLogger("data_analytics_platform.http")
_VALID_REQUEST_ID = re.compile(r"^[A-Za-z0-9._-]{1,128}$")


def _resolve_request_id(request: Request) -> str:
    candidate = request.headers.get("X-Request-ID", "")
    return candidate if _VALID_REQUEST_ID.fullmatch(candidate) else str(uuid4())


class RequestContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        request_id = _resolve_request_id(request)
        request.state.request_id = request_id
        token = bind_request_id(request_id)
        started_at = time.perf_counter()
        status = 500
        try:
            try:
                response = await call_next(request)
            except Exception:
                logger.exception("unexpected request error")
                response = unexpected_error_response(request_id)
            status = response.status_code
            response.headers["X-Request-ID"] = request_id
            return response
        finally:
            duration_ms = round((time.perf_counter() - started_at) * 1000, 2)
            logger.info(
                "request completed",
                extra={
                    "method": request.method,
                    "path": request.url.path,
                    "status": status,
                    "duration_ms": duration_ms,
                },
            )
            reset_request_id(token)
