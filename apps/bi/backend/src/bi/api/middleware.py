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
            response.headers["X-Content-Type-Options"] = "nosniff"
            response.headers["Referrer-Policy"] = "no-referrer"
            response.headers["X-Frame-Options"] = "DENY"
            response.headers["Cache-Control"] = "no-store"
            return response
        finally:
            duration_ms = round((time.perf_counter() - started_at) * 1000, 2)
            logger.info(
                "request completed",
                extra={
                    "method": request.method,
                    "path": getattr(request.scope.get("route"), "path", "/unmatched"),
                    "status": status,
                    "duration_ms": duration_ms,
                },
            )
            reset_request_id(token)


class RuntimeLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        from ipaddress import ip_address
        from analytics_core.errors import AppError
        from bi.api.error_handlers import app_error_handler
        settings = request.app.state.settings
        peer = request.client.host if request.client else "unknown"
        client_ip = peer
        if peer in settings.trusted_proxy_ips:
            try:
                chain = [str(ip_address(item.strip())) for item in request.headers.get("X-Forwarded-For", "").split(",") if item.strip()]
                for address in reversed(chain):
                    client_ip = address
                    if address not in settings.trusted_proxy_ips: break
            except ValueError:
                client_ip = peer
        request.state.client_ip = client_ip
        if request.method == "POST" and request.url.path in {f"{settings.api_prefix}/datasets", f"{settings.api_prefix}/datasets/demo"}:
            try:
                length = request.headers.get("Content-Length")
                if length is not None:
                    try: size = int(length)
                    except ValueError:
                        raise AppError(code="FILE_CORRUPT", http_status=400, message="El tamaño declarado no es válido.")
                    if size < 0:
                        raise AppError(code="FILE_CORRUPT", http_status=400, message="El tamaño declarado no es válido.")
                    if size > settings.max_file_mb * 1024 * 1024 + settings.multipart_overhead_bytes:
                        raise AppError(code="FILE_TOO_LARGE", http_status=413, message="La carga supera el máximo permitido.")
                request.app.state.runtime.check_rate(client_ip)
            except AppError as exc:
                return await app_error_handler(request, exc)
        return await call_next(request)


class UploadBodyLimitMiddleware:
    """Bound the complete multipart body before FastAPI parses/spools it."""
    def __init__(self, app, settings):
        self.app, self.settings = app, settings

    async def __call__(self, scope, receive, send):
        targets = {f"{self.settings.api_prefix}/datasets", f"{self.settings.api_prefix}/datasets/demo"}
        if scope["type"] != "http" or scope["method"] != "POST" or scope["path"] not in targets:
            return await self.app(scope, receive, send)
        from tempfile import SpooledTemporaryFile
        from analytics_core.sources.upload import UploadSource
        from analytics_core.errors import AppError
        from bi.api.error_handlers import app_error_handler
        limit = self.settings.max_file_mb * 1024 * 1024 + self.settings.multipart_overhead_bytes
        with SpooledTemporaryFile(max_size=UploadSource.chunk_size) as spool:
            size = 0
            while True:
                event = await receive()
                if event["type"] == "http.disconnect": return
                chunk = event.get("body", b"")
                size += len(chunk)
                if size > limit:
                    error = AppError(code="FILE_TOO_LARGE", http_status=413, message="La carga supera el máximo permitido.")
                    response = await app_error_handler(Request(scope), error)
                    return await response(scope, receive, send)
                spool.write(chunk)
                if not event.get("more_body", False): break
            spool.seek(0)
            finished = False
            async def replay():
                nonlocal finished
                if finished: return await receive()
                chunk = spool.read(UploadSource.chunk_size)
                finished = spool.tell() == size
                return {"type": "http.request", "body": chunk, "more_body": not finished}
            return await self.app(scope, replay, send)
