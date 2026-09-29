"""Explicit and testable profile registry."""

from analytics_core.canonical.fields import UNIVERSAL_FIELDS, FieldSpec
from analytics_core.mapping.matcher import normalize_name
from bi.profiles.base import IndustryProfile

_profiles: dict[str, IndustryProfile] = {}


def profile_fields(profile: IndustryProfile) -> list[FieldSpec]:
    catalog = {field.id: field for field in UNIVERSAL_FIELDS}
    catalog.update({field.id: field for field in profile.data.extension_fields})
    return [catalog[rule.field_id] for rule in profile.data.fields]


def register_profile(profile: IndustryProfile) -> None:
    if profile.id in _profiles:
        raise ValueError(f"duplicate profile id: {profile.id}")
    catalog = {field.id: field for field in UNIVERSAL_FIELDS}
    for extension in profile.data.extension_fields:
        if extension.id in catalog and catalog[extension.id] != extension:
            raise ValueError(f"field collision: {extension.id}")
        catalog[extension.id] = extension
    referenced = {rule.field_id for rule in profile.data.fields}
    if not referenced <= set(catalog):
        raise ValueError("profile references unknown fields")
    if profile.data.primary_date not in referenced or not set(profile.data.alternate_dates) <= referenced:
        raise ValueError("invalid profile date fields")
    alias_owner: dict[str, str] = {}
    for field_id, aliases in profile.data.aliases.items():
        if field_id not in referenced:
            raise ValueError(f"aliases reference unknown field: {field_id}")
        for alias in [field_id, *aliases]:
            normalized = normalize_name(alias)
            owner = alias_owner.get(normalized)
            if owner and owner != field_id:
                raise ValueError(f"alias collision: {alias}")
            alias_owner[normalized] = field_id
    _profiles[profile.id] = profile


def get_profile(profile_id: str) -> IndustryProfile:
    try:
        return _profiles[profile_id]
    except KeyError as exc:
        raise KeyError(f"unknown profile: {profile_id}") from exc


def list_profiles() -> list[IndustryProfile]:
    return sorted(_profiles.values(), key=lambda profile: profile.id)


def clear_profiles() -> None:
    _profiles.clear()
