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


class IndustryProfile(BaseModel, frozen=True):
    id: str
    version: str = "1.0"
    name: str
    description: str
    data: ProfileData
