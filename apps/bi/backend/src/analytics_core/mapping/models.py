"""Transport-neutral mapping models."""

from enum import StrEnum
from typing import Any, Literal

from pydantic import BaseModel, Field, model_validator


class ColumnDisposition(StrEnum):
    canonical = "canonical"
    custom_dimension = "custom_dimension"
    custom_measure = "custom_measure"
    ignored = "ignored"


class ColumnMapping(BaseModel):
    column_key: str
    target_field: str | None = None
    disposition: ColumnDisposition
    options: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def target_matches_disposition(self) -> "ColumnMapping":
        if self.disposition == ColumnDisposition.canonical and not self.target_field:
            raise ValueError("canonical mappings require target_field")
        if self.disposition != ColumnDisposition.canonical and self.target_field:
            raise ValueError("custom or ignored mappings cannot have target_field")
        return self


class MappingCandidate(BaseModel):
    field_id: str
    score: float = Field(ge=0, le=1)
    confidence: Literal["high", "medium", "low"]
    reasons: list[str]


class MappingSuggestion(BaseModel):
    column_key: str
    candidates: list[MappingCandidate] = Field(default_factory=list)
    suggested_disposition: ColumnDisposition | None = None


class MappingConflict(BaseModel):
    code: str
    severity: Literal["error", "warning", "info"]
    message: str
    column_key: str | None = None
    field_id: str | None = None
