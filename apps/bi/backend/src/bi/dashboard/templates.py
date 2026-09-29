"""Typed, moderate dashboard configuration."""

from typing import Literal
from pydantic import BaseModel, Field


class LayoutSpec(BaseModel, frozen=True):
    span: int = Field(default=6, ge=1, le=12)


class WidgetTemplate(BaseModel, frozen=True):
    id: str
    type: Literal["kpi", "timeseries", "breakdown", "ranking", "table", "insights", "quality"]
    title_key: str
    metric_id: str | None = None
    dimension: str | None = None
    top_n: int | None = None
    chart_variant: Literal["bar", "donut", "line", "area"] | None = None
    required_fields: tuple[str, ...] = ()
    layout: LayoutSpec = LayoutSpec()


class SectionTemplate(BaseModel, frozen=True):
    id: str
    title_key: str
    collapsed: bool = False
    widgets: tuple[WidgetTemplate, ...] = ()
    visible_if_fields: tuple[str, ...] = ()


class DashboardTemplate(BaseModel, frozen=True):
    sections: tuple[SectionTemplate, ...]
