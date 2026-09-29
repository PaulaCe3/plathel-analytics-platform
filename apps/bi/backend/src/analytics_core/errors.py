"""Application-safe error types shared by API-facing products."""

from collections.abc import Mapping, Sequence
from typing import Any


class AppError(Exception):
    """A controlled error whose public fields are safe to return to a client."""

    def __init__(
        self,
        *,
        code: str,
        http_status: int,
        message: str,
        details: Sequence[Mapping[str, Any]] | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.http_status = http_status
        self.message = message
        self.details = [dict(detail) for detail in details or []]
