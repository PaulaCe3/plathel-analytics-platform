"""Minimal declarative derived-field infrastructure."""

from typing import Literal

from pydantic import BaseModel


class DerivedFieldRule(BaseModel, frozen=True):
    id: str
    target_field: str
    operation: Literal["multiply"]
    source_fields: tuple[str, str]


UNIVERSAL_DERIVED_RULES = (
    DerivedFieldRule(id="amount_from_unit_price_quantity", target_field="amount", operation="multiply", source_fields=("unit_price", "quantity")),
)


def resolvable_fields(available: set[str], rules: tuple[DerivedFieldRule, ...] = UNIVERSAL_DERIVED_RULES) -> set[str]:
    resolved = set(available)
    changed = True
    while changed:
        changed = False
        for rule in rules:
            if rule.target_field not in resolved and set(rule.source_fields) <= resolved:
                resolved.add(rule.target_field)
                changed = True
    return resolved
