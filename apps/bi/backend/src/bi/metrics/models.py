"""Metric definitions and neutral result contracts."""

from datetime import date
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, PrivateAttr

from bi.metrics.expr import Expr, required_fields


class OutputSpec(BaseModel, frozen=True):
    type: Literal["currency", "number", "integer", "percent", "duration"]
    decimals: int = 0
    currency: str | None = None


class MetricDefinition(BaseModel, frozen=True):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    id: str
    label_key: str
    description_key: str
    group: str
    expr: Expr
    output: OutputSpec
    industries: list[str] | None = None
    comparable: bool = True
    additive: bool = True
    polarity: Literal["higher_is_better", "lower_is_better", "neutral"] = "higher_is_better"
    currency_sensitive: bool = False
    _expr_resolver: object | None = PrivateAttr(default=None)

    @property
    def requires(self) -> set[str]:
        resolver = self._expr_resolver if callable(self._expr_resolver) else None
        return required_fields(self.expr, resolver)


class MetricWarning(BaseModel, frozen=True):
    code: str
    message_key: str


ComparisonMode = Literal["none", "previous_period", "previous_week", "previous_month", "previous_quarter", "previous_year"]


class DateRange(BaseModel, frozen=True):
    from_date: date = Field(alias="from")
    to_date: date = Field(alias="to")

    model_config = {"populate_by_name": True}


class ComparisonSpec(BaseModel, frozen=True):
    mode: ComparisonMode = "previous_period"


class ComparisonResult(BaseModel, frozen=True):
    mode: ComparisonMode
    status: Literal["ok", "insufficient_data", "previous_zero", "not_applicable"]
    current_range: DateRange | None = None
    reason_key: str | None = None
    percentage_reason_key: str | None = None
    delta_pp: float | None = None
    direction: Literal["increase", "decrease", "unchanged"] | None = None
    polarity: Literal["higher_is_better", "lower_is_better", "neutral"] = "neutral"
    previous_value: float | None = None
    delta_abs: float | None = None
    delta_pct: float | None = None
    previous_range: DateRange | None = None
    partial_period: bool = False
    warnings: list[MetricWarning] = Field(default_factory=list)


class UnavailableMetric(BaseModel, frozen=True):
    reason_key: str | None = None
    metric_id: str
    missing_fields: list[str]
    label_key: str | None = None


class MetricAvailability(BaseModel, frozen=True):
    reason_key: str | None = None
    available: bool
    missing_fields: list[str] = Field(default_factory=list)


class MetricResult(BaseModel, frozen=True):
    metric_id: str
    label_key: str
    status: Literal["ok", "unavailable", "empty", "error"]
    value: float | int | None = None
    format: OutputSpec
    excluded_rows: int = 0
    warnings: list[MetricWarning] = Field(default_factory=list)
    comparison: ComparisonResult | None = None
