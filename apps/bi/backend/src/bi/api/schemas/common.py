"""Schemas shared across system endpoints."""

from typing import Any

from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str


class ErrorBody(BaseModel):
    code: str
    message: str
    details: list[dict[str, Any]]
    request_id: str


class ErrorResponse(BaseModel):
    error: ErrorBody
