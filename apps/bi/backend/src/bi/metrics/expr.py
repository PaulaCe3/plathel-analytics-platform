"""Closed, typed expression tree for BI metrics."""

from dataclasses import dataclass
from typing import Callable


class Expr:
    """Marker base class; expressions are data, never executable text."""


@dataclass(frozen=True)
class Field(Expr):
    id: str


@dataclass(frozen=True, init=False)
class AnyOf(Expr):
    fields: tuple[str, ...]

    def __init__(self, *fields: str):
        if not fields:
            raise ValueError("AnyOf requires at least one field")
        object.__setattr__(self, "fields", tuple(fields))


@dataclass(frozen=True)
class Sum(Expr):
    value: Expr


@dataclass(frozen=True)
class Mean(Expr):
    value: Expr


@dataclass(frozen=True)
class Count(Expr):
    pass


@dataclass(frozen=True)
class CountDistinct(Expr):
    value: Expr
    fallback: Expr | None = None


@dataclass(frozen=True)
class Min(Expr):
    value: Expr


@dataclass(frozen=True)
class Max(Expr):
    value: Expr


@dataclass(frozen=True)
class Ratio(Expr):
    numerator: Expr
    denominator: Expr


@dataclass(frozen=True)
class Sub(Expr):
    left: Expr
    right: Expr


@dataclass(frozen=True)
class RowMul(Expr):
    left: Expr
    right: Expr


@dataclass(frozen=True)
class MetricRef(Expr):
    id: str


def field_options(expr: Expr, resolve_metric: Callable[[str], Expr] | None = None) -> tuple[frozenset[str], ...]:
    """Return AND-ed requirements, where each set contains OR-ed field choices."""
    if isinstance(expr, Field):
        return (frozenset((expr.id,)),)
    if isinstance(expr, AnyOf):
        return (frozenset(expr.fields),)
    if isinstance(expr, (Count,)):
        return ()
    if isinstance(expr, (Sum, Mean, Min, Max)):
        return field_options(expr.value, resolve_metric)
    if isinstance(expr, CountDistinct):
        primary = field_options(expr.value, resolve_metric)
        return () if expr.fallback is not None else primary
    if isinstance(expr, (Ratio,)):
        return (*field_options(expr.numerator, resolve_metric), *field_options(expr.denominator, resolve_metric))
    if isinstance(expr, (Sub, RowMul)):
        return (*field_options(expr.left, resolve_metric), *field_options(expr.right, resolve_metric))
    if isinstance(expr, MetricRef):
        return field_options(resolve_metric(expr.id), resolve_metric) if resolve_metric else ()
    raise TypeError(f"Unsupported expression: {type(expr).__name__}")


def required_fields(expr: Expr, resolve_metric: Callable[[str], Expr] | None = None) -> set[str]:
    return set().union(*field_options(expr, resolve_metric)) if field_options(expr, resolve_metric) else set()

