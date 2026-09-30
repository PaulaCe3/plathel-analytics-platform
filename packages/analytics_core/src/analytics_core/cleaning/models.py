"""Declarative cleaning and audit models."""

from datetime import UTC, datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


class CleaningActionSpec(BaseModel):
    id: Literal["trim_whitespace", "parse_dates", "parse_numbers", "drop_empty_columns", "drop_exact_duplicates", "drop_rows"]
    params: dict[str, Any] = Field(default_factory=dict)
    destructive: bool = False
    selected: bool = False
    estimated_rows_affected: int = 0
    estimated_values_affected: int = 0
    description: str


class CleaningPlan(BaseModel):
    actions: list[CleaningActionSpec] = Field(default_factory=list)


class TransformationExample(BaseModel):
    row_id: int | None = None
    before: str | None = None
    after: str | None = None


class Transformation(BaseModel):
    id: str
    seq: int
    action_id: str
    kind: Literal["parse", "normalize", "derive", "remove", "fill"]
    columns: list[str] = Field(default_factory=list)
    params: dict[str, Any] = Field(default_factory=dict)
    rows_before: int
    rows_after: int
    rows_affected: int
    summary: str
    examples: list[TransformationExample] = Field(default_factory=list, max_length=3)
    automatic: bool
    at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class TransformationLog(BaseModel):
    transformations: list[Transformation] = Field(default_factory=list)


class CanonicalBuildResult(BaseModel):
    row_count: int
    column_count: int
    columns: list[str]
    parse_reports: list["ParseReport"]
    transformations: list[Transformation]


from analytics_core.validation.models import ParseReport  # noqa: E402

CanonicalBuildResult.model_rebuild()
