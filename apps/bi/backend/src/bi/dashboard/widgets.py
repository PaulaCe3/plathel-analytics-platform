"""Neutral dashboard contracts; no chart-library types."""

from datetime import datetime
from typing import Any, Literal
from pydantic import BaseModel, Field

from bi.metrics.models import MetricResult, UnavailableMetric
from bi.insights.engine import Insight
from bi.metrics.models import ComparisonSpec
from analytics_core.engine.query import FilterClause
from bi.dashboard.templates import LayoutSpec


class FilterOption(BaseModel, frozen=True):
    value: str
    count: int


class FilterDefinition(BaseModel, frozen=True):
    id: str
    field: str
    type: Literal["date_range", "multi_select", "search"]
    label_key: str
    options: list[FilterOption] = Field(default_factory=list)
    minimum: str | None = None
    maximum: str | None = None
    presets: list[str] = Field(default_factory=list)


class ComparisonOption(BaseModel, frozen=True):
    mode: str
    available: bool
    reason_key: str | None = None


class WidgetSpec(BaseModel, frozen=True):
    id: str
    type: str
    title_key: str
    chart_variant: str | None = None
    layout: LayoutSpec = LayoutSpec()


class SectionSpec(BaseModel, frozen=True):
    id: str
    title_key: str
    collapsed: bool = False
    widgets: list[WidgetSpec]


class DashboardSpec(BaseModel, frozen=True):
    profile_id: str
    sections: list[SectionSpec]
    filters: list[FilterDefinition]
    unavailable_metrics: list[UnavailableMetric]
    comparison_options: list[ComparisonOption]
    terminology: dict[str, str] = Field(default_factory=dict)
    key_chart_ids: list[str] = Field(default_factory=list)


class ChartSeries(BaseModel, frozen=True):
    key: str
    label_key: str
    points: list[list[Any]]


class ChartResult(BaseModel, frozen=True):
    status: Literal["ok", "empty", "unavailable", "error"]
    widget_id: str
    chart: Literal["timeseries", "breakdown", "ranking"]
    x_type: Literal["time", "category"]
    grain: str | None = None
    series: list[ChartSeries] = Field(default_factory=list)
    comparison_series: list[ChartSeries] = Field(default_factory=list)
    meta: dict[str, Any] = Field(default_factory=dict)
    error_key: str | None = None
    interpretation: Insight | None = None


class TableResult(BaseModel, frozen=True):
    status: Literal["ok", "empty", "unavailable", "error"]
    widget_id: str
    columns: list[str] = Field(default_factory=list)
    rows: list[dict[str, Any]] = Field(default_factory=list)
    error_key: str | None = None


class QualityResult(BaseModel, frozen=True):
    status: Literal["ok", "empty", "unavailable", "error"] = "ok"
    widget_id: str
    total_issues: int = 0
    error_count: int = 0
    warning_count: int = 0
    info_count: int = 0


class InsightsResult(BaseModel, frozen=True):
    status: Literal["ok", "empty", "unavailable", "error"]
    widget_id: str
    insights: list[Insight] = Field(default_factory=list)


class DashboardResponse(BaseModel):
    spec: DashboardSpec
    data: dict[str, MetricResult | ChartResult | InsightsResult | TableResult | QualityResult | Any]
    row_count: int
    filtered_row_count: int
    warnings: list[dict[str, Any]] = Field(default_factory=list)
    generated_at: datetime


class DashboardRequest(BaseModel):
    filters: list[FilterClause] = Field(default_factory=list)
    comparison: ComparisonSpec = ComparisonSpec()
    time_field: str | None = None
    grain: Literal["auto", "day", "week", "month", "quarter", "year"] = "auto"
