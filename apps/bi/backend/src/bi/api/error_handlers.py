"""Consistent, non-technical error responses for the HTTP boundary."""

import logging

from fastapi import Request
from fastapi.responses import JSONResponse

from analytics_core.errors import AppError

logger = logging.getLogger("data_analytics_platform.api")


def _request_id(request: Request) -> str:
    return getattr(request.state, "request_id", "unknown")


def error_response(
    *, code: str, message: str, details: list[dict[str, object]], request_id: str, status: int
) -> JSONResponse:
    return JSONResponse(
        status_code=status,
        content={
            "error": {
                "code": code,
                "message": message,
                "details": details,
                "request_id": request_id,
            }
        },
    )


async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    return error_response(
        code=exc.code,
        message=exc.message,
        details=exc.details,
        request_id=_request_id(request),
        status=exc.http_status,
    )


def unexpected_error_response(request_id: str) -> JSONResponse:
    return error_response(
        code="INTERNAL_ERROR",
        message="Se produjo un error interno. Intentá nuevamente.",
        details=[],
        request_id=request_id,
        status=500,
    )


async def unexpected_error_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("unexpected request error")
    return unexpected_error_response(_request_id(request))
