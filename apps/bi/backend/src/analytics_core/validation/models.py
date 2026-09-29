"""Read-only validation domain models."""

from typing import Any, Literal

from pydantic import BaseModel, Field


class Issue(BaseModel):
    id: str
    code: str
    scope: Literal["dataset", "field", "row", "profile"]
    severity: Literal["error", "warning", "info"]
    message: str
    field_id: str | None = None
    column_key: str | None = None
    count: int | None = None
    ratio: float | None = None
    sample_row_ids: list[int] = Field(default_factory=list, max_length=10)
    suggested_action: str | None = None
    category: str = "validation"


class ParseReport(BaseModel):
    total_rows: int
    parsed_rows: int
    invalid_rows: int
    invalid_ratio: float
    field_id: str
    source_column_key: str
    parse_type: str
    sample_row_ids: list[int] = Field(default_factory=list, max_length=10)


class ValidationReport(BaseModel):
    valid: bool
    issues: list[Issue] = Field(default_factory=list)
    blocking_count: int = 0
    warning_count: int = 0
    info_count: int = 0
    parse_reports: list[ParseReport] = Field(default_factory=list)


class ProfileCheck(BaseModel, frozen=True):
    id: str
    operation: Literal["greater_than"]
    left_field: str
    right_field: str
    severity: Literal["error", "warning", "info"] = "warning"
    message: str


def validation_report(issues: list[Issue], parse_reports: list[ParseReport]) -> ValidationReport:
    blocking = sum(issue.severity == "error" for issue in issues)
    return ValidationReport(
        valid=blocking == 0,
        issues=issues,
        blocking_count=blocking,
        warning_count=sum(issue.severity == "warning" for issue in issues),
        info_count=sum(issue.severity == "info" for issue in issues),
        parse_reports=parse_reports,
    )
