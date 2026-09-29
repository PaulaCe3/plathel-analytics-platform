"""Small helpers used only while declaring concrete profiles."""

from analytics_core.canonical.fields import FieldSpec
from bi.profiles.base import ProfileFieldRule


def rules(required: list[str], recommended: list[str], optional: list[str]) -> tuple[ProfileFieldRule, ...]:
    return tuple(
        [ProfileFieldRule(field_id=field, level="required") for field in required]
        + [ProfileFieldRule(field_id=field, level="recommended") for field in recommended]
        + [ProfileFieldRule(field_id=field, level="optional") for field in optional]
    )


def extension(field_id: str, kind: str, dtype: str) -> FieldSpec:
    return FieldSpec(id=field_id, label_key=f"field.{field_id}", kind=kind, dtype=dtype, scope="extension")
