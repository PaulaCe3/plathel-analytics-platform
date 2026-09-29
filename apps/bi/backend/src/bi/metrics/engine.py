"""Metric evaluation over the backend-neutral DataEngine contract."""

from dataclasses import dataclass
from pathlib import Path

from analytics_core.engine.base import DataEngine
from analytics_core.engine.query import FilterClause, GroupBy, MeasureSpec, QuerySpec
from bi.metrics.availability import resolve_availability
from bi.metrics.expr import AnyOf, Count, CountDistinct, Expr, Field, Max, Mean, MetricRef, Min, Ratio, RowMul, Sub, Sum
from bi.metrics.models import MetricResult, MetricWarning
from bi.metrics.registry import MetricRegistry


@dataclass(frozen=True)
class _Value:
    value: float | int | None
    excluded_rows: int = 0
    warnings: tuple[MetricWarning, ...] = ()

    def with_warnings(self, warnings: tuple[MetricWarning, ...]) -> "_Value":
        return _Value(self.value, self.excluded_rows, (*self.warnings, *warnings))


class MetricEngine:
    def __init__(self, data_engine: DataEngine, registry: MetricRegistry):
        self.data_engine = data_engine
        self.registry = registry

    def evaluate(
        self,
        canonical_path: Path,
        metric_id: str,
        available_fields: set[str],
        filters: list[FilterClause] | None = None,
    ) -> MetricResult:
        metric = self.registry.get(metric_id)
        availability = resolve_availability(self.registry, available_fields)[metric_id]
        if not availability.available:
            return MetricResult(metric_id=metric.id, label_key=metric.label_key, status="unavailable", format=metric.output)
        selected_filters = filters or []
        if metric.currency_sensitive and "currency" in available_fields and self._has_mixed_currency(canonical_path, selected_filters):
            return MetricResult(
                metric_id=metric.id,
                label_key=metric.label_key,
                status="unavailable",
                format=metric.output,
                warnings=[MetricWarning(code="MIXED_CURRENCY", message_key="warning.mixed_currency")],
            )
        value = self._evaluate_expr(canonical_path, metric.expr, available_fields, selected_filters, set())
        status = "empty" if value.value is None else "ok"
        return MetricResult(metric_id=metric.id, label_key=metric.label_key, status=status, value=value.value, format=metric.output, excluded_rows=value.excluded_rows, warnings=list(value.warnings))

    def _has_mixed_currency(self, path: Path, filters: list[FilterClause]) -> bool:
        query = QuerySpec(measures=[MeasureSpec(alias="rows", aggregation="count")], group_by=[GroupBy(field="currency")], filters=filters, limit=2)
        result = self.data_engine.run_query(path, query)
        currencies = [row.get("currency") for row in result.rows if row.get("currency") not in (None, "")]
        return len(currencies) > 1

    def _field(self, expr: Expr, available: set[str]) -> str | None:
        if isinstance(expr, Field):
            return expr.id if expr.id in available else None
        if isinstance(expr, AnyOf):
            return next((field for field in expr.fields if field in available), None)
        return None

    def _aggregate(self, path: Path, expression: Expr, available: set[str], filters: list[FilterClause], alias: str) -> _Value:
        aggregation: str
        field: str | None = None
        fields: tuple[str, str] | None = None
        fallback_warning: tuple[MetricWarning, ...] = ()
        if isinstance(expression, Count):
            aggregation = "count"
        elif isinstance(expression, CountDistinct):
            field = self._field(expression.value, available)
            if field is None and expression.fallback is not None:
                fallback_warning = (MetricWarning(code="COUNT_FALLBACK", message_key="warning.transactions_count_fallback"),)
                return self._aggregate(path, expression.fallback, available, filters, alias).with_warnings(fallback_warning)
            aggregation = "count_distinct"
        elif isinstance(expression, (Sum, Mean, Min, Max)):
            if isinstance(expression.value, RowMul):
                left = self._field(expression.value.left, available)
                right = self._field(expression.value.right, available)
                fields = (left or "", right or "")
                aggregation = "row_mul_sum"
            else:
                field = self._field(expression.value, available)
                aggregation = {Sum: "sum", Mean: "mean", Min: "min", Max: "max"}[type(expression)]
        else:
            raise TypeError(f"Not an aggregate expression: {type(expression).__name__}")
        measure = MeasureSpec(alias=alias, aggregation=aggregation, field=field, fields=fields)
        result = self.data_engine.run_query(path, QuerySpec(measures=[measure], filters=filters))
        raw = result.rows[0].get(alias) if result.rows else None
        return _Value(value=raw if isinstance(raw, (int, float)) else None, excluded_rows=result.excluded_rows.get(alias, 0), warnings=fallback_warning)

    def _evaluate_expr(self, path: Path, expr: Expr, available: set[str], filters: list[FilterClause], stack: set[str]) -> _Value:
        if isinstance(expr, (Sum, Mean, Count, CountDistinct, Min, Max)):
            return self._aggregate(path, expr, available, filters, "value")
        if isinstance(expr, MetricRef):
            if expr.id in stack:
                raise ValueError(f"Cyclic metric reference: {expr.id}")
            return self._evaluate_expr(path, self.registry.get(expr.id).expr, available, filters, {*stack, expr.id})
        if isinstance(expr, (Ratio, Sub)):
            left_expr, right_expr = (expr.numerator, expr.denominator) if isinstance(expr, Ratio) else (expr.left, expr.right)
            left = self._evaluate_expr(path, left_expr, available, filters, stack)
            right = self._evaluate_expr(path, right_expr, available, filters, stack)
            warnings = (*left.warnings, *right.warnings)
            excluded = max(left.excluded_rows, right.excluded_rows)
            if left.value is None or right.value is None:
                return _Value(None, excluded, warnings)
            if isinstance(expr, Ratio):
                return _Value(None if right.value == 0 else float(left.value) / float(right.value), excluded, warnings)
            return _Value(float(left.value) - float(right.value), excluded, warnings)
        raise TypeError(f"Expression must aggregate fields: {type(expr).__name__}")
