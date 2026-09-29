"""Typed data-only industry profiles for mapping."""

from typing import Literal

from pydantic import BaseModel, Field

from analytics_core.canonical.fields import FieldSpec
from analytics_core.validation.models import ProfileCheck


class ProfileFieldRule(BaseModel, frozen=True):
    field_id: str
    level: Literal["required", "recommended", "optional"]


class ProfileData(BaseModel, frozen=True):
    fields: tuple[ProfileFieldRule, ...]
    extension_fields: tuple[FieldSpec, ...] = ()
    aliases: dict[str, list[str]] = Field(default_factory=dict)
    terminology: dict[str, dict[str, str]] = Field(default_factory=dict)
    primary_date: str = "date"
    alternate_dates: tuple[str, ...] = ()
    checks: tuple[ProfileCheck, ...] = ()


class BIWidgetConfig(BaseModel, frozen=True):
    id: str
    type: Literal["kpi", "timeseries", "breakdown", "ranking", "table", "insights", "quality"]
    title_key: str
    metric_id: str | None = None
    dimension: str | None = None
    top_n: int | None = None
    chart_variant: Literal["bar", "donut", "line", "area"] | None = None
    required_fields: tuple[str, ...] = ()


class BIConfig(BaseModel, frozen=True):
    metrics: tuple[str, ...] = ("revenue", "transactions", "customers", "avg_transaction_value", "quantity", "avg_unit_price")
    kpi_order: tuple[str, ...] = ("revenue", "transactions", "customers", "avg_transaction_value", "quantity", "avg_unit_price")
    featured_dimensions: tuple[str, ...] = ()
    widgets: tuple[BIWidgetConfig, ...] = ()
    insight_rules: tuple[str, ...] = ("growth_vs_previous", "leader_share", "top_n_concentration", "peak_period", "channel_dominance", "data_quality_alert")
    extra_filters: tuple[str, ...] = ()


class IndustryProfile(BaseModel, frozen=True):
    id: str
    version: str = "1.0"
    name: str
    description: str
    data: ProfileData
    bi: BIConfig | None = None
