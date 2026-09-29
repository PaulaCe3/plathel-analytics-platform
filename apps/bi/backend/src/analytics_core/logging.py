"""Central logging primitives with request correlation and safe structured fields."""

from __future__ import annotations

import json
import logging
from contextvars import ContextVar, Token
from datetime import UTC, datetime
from typing import Any

_request_id: ContextVar[str] = ContextVar("request_id", default="-")
_EXTRA_FIELDS = ("method", "path", "status", "duration_ms")


def bind_request_id(request_id: str) -> Token[str]:
    return _request_id.set(request_id)


def reset_request_id(token: Token[str]) -> None:
    _request_id.reset(token)


def current_request_id() -> str:
    return _request_id.get()


class RequestIdFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = current_request_id()
        return True


class JsonFormatter(logging.Formatter):
    """Small JSON formatter using only the Python standard library."""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": datetime.now(UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "request_id": getattr(record, "request_id", "-"),
        }
        for field in _EXTRA_FIELDS:
            value = getattr(record, field, None)
            if value is not None:
                payload[field] = value
        return json.dumps(payload, ensure_ascii=False)


def configure_logging(level: str = "INFO") -> None:
    logger = logging.getLogger("data_analytics_platform")
    handler = logging.StreamHandler()
    handler.addFilter(RequestIdFilter())
    handler.setFormatter(JsonFormatter())
    logger.handlers.clear()
    logger.addHandler(handler)
    logger.setLevel(level.upper())
    logger.propagate = False
