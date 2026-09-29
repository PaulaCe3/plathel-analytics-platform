"""Declarative universal field catalog. No field is globally required."""

from typing import Literal

from pydantic import BaseModel

FieldKind = Literal["identifier", "dimension", "measure", "time"]
FieldDtype = Literal["string", "integer", "decimal", "date", "datetime", "boolean"]
FieldScope = Literal["universal", "extension", "custom"]


class FieldSpec(BaseModel, frozen=True):
    id: str
    label_key: str
    kind: FieldKind
    dtype: FieldDtype
    description_key: str | None = None
    scope: FieldScope = "universal"


def _field(field_id: str, kind: FieldKind, dtype: FieldDtype) -> FieldSpec:
    return FieldSpec(id=field_id, label_key=f"field.{field_id}", description_key=f"field.{field_id}.description", kind=kind, dtype=dtype)


UNIVERSAL_FIELDS: tuple[FieldSpec, ...] = (
    _field("date", "time", "date"),
    _field("transaction_id", "identifier", "string"),
    _field("customer_id", "identifier", "string"),
    _field("customer_name", "dimension", "string"),
    _field("concept", "dimension", "string"),
    _field("category", "dimension", "string"),
    _field("subcategory", "dimension", "string"),
    _field("amount", "measure", "decimal"),
    _field("quantity", "measure", "decimal"),
    _field("unit_price", "measure", "decimal"),
    _field("cost", "measure", "decimal"),
    _field("discount", "measure", "decimal"),
    _field("channel", "dimension", "string"),
    _field("location", "dimension", "string"),
    _field("responsible", "dimension", "string"),
    _field("status", "dimension", "string"),
    _field("currency", "dimension", "string"),
)

_BY_ID = {field.id: field for field in UNIVERSAL_FIELDS}


def get_universal_field(field_id: str) -> FieldSpec | None:
    return _BY_ID.get(field_id)
