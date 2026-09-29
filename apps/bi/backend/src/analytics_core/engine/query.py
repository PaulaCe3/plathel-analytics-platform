"""Backend-neutral query contracts."""

from datetime import date, datetime
from typing import Any, Literal

from pydantic import BaseModel, Field, model_validator

Scalar = str | int | float | bool | date | datetime | None
Aggregation = Literal["sum", "mean", "count", "count_distinct", "min", "max", "row_mul_sum"]


class MeasureSpec(BaseModel, frozen=True):
    alias: str
    aggregation: Aggregation
    field: str | None = None
    fields: tuple[str, str] | None = None

    @model_validator(mode="after")
    def validate_operands(self) -> "MeasureSpec":
        if self.aggregation == "count":
            return self
        if self.aggregation == "row_mul_sum":
            if self.fields is None:
                raise ValueError("row_mul_sum requires two fields")
            return self
        if self.field is None:
            raise ValueError(f"{self.aggregation} requires a field")
        return self

    @property
    def required_fields(self) -> tuple[str, ...]:
        if self.aggregation == "count":
            return ()
        if self.aggregation == "row_mul_sum":
            return self.fields or ()
        return (self.field,) if self.field else ()


class GroupBy(BaseModel, frozen=True):
    field: str
    grain: Literal["day", "week", "month", "quarter", "year"] | None = None


class FilterClause(BaseModel, frozen=True):
    field: str
    op: Literal["in", "not_in", "between", "gte", "lte", "contains"]
    values: list[Any]

    @model_validator(mode="after")
    def validate_values(self) -> "FilterClause":
        required = 2 if self.op == "between" else 1
        if len(self.values) < required:
            raise ValueError(f"{self.op} requires at least {required} value(s)")
        return self


class OrderBy(BaseModel, frozen=True):
    field: str
    direction: Literal["asc", "desc"] = "asc"


class QuerySpec(BaseModel, frozen=True):
    measures: list[MeasureSpec]
    group_by: list[GroupBy] = Field(default_factory=list)
    filters: list[FilterClause] = Field(default_factory=list)
    order_by: list[OrderBy] = Field(default_factory=list)
    limit: int | None = Field(default=None, ge=1)
    others_bucket: bool = False


class QueryResult(BaseModel, frozen=True):
    columns: list[str]
    rows: list[dict[str, Scalar]]
    row_count: int
    excluded_rows: dict[str, int] = Field(default_factory=dict)


class DateCoverage(BaseModel, frozen=True):
    minimum: date | None = None
    maximum: date | None = None

