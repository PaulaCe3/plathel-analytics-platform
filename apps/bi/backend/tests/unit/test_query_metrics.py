from datetime import date, datetime

import pyarrow as pa
import pyarrow.parquet as pq

from analytics_core.engine.pandas_impl.engine import PandasDataEngine
from analytics_core.engine.query import FilterClause, GroupBy, MeasureSpec, OrderBy, QuerySpec
from bi.metrics.availability import resolve_availability
from bi.metrics.comparison import ComparisonResolver
from bi.metrics.engine import MetricEngine
from bi.metrics.expr import AnyOf, Count, CountDistinct, Field, Max, Mean, MetricRef, Min, Ratio, RowMul, Sub, Sum
from bi.metrics.models import DateRange, MetricDefinition, OutputSpec
from bi.metrics.registry import MetricRegistry
from bi.metrics.universal import build_universal_registry


def _parquet(tmp_path):
    path = tmp_path / "canonical.parquet"
    table = pa.table(
        {
            "date": pa.array([datetime(2025, 1, 1), datetime(2025, 1, 8), datetime(2025, 2, 1), datetime(2025, 2, 2)]),
            "amount": [100.0, 50.0, 30.0, None],
            "_valid__amount": [True, True, True, False],
            "quantity": [2.0, 1.0, 3.0, 4.0],
            "_valid__quantity": [True, True, True, True],
            "transaction_id": ["a", "b", "c", "d"],
            "_valid__transaction_id": [True, True, True, True],
            "customer_name": ["Ana", "Ana", "Bob", "Cid"],
            "_valid__customer_name": [True, True, True, True],
            "customer_id": ["1", "1", "2", "3"],
            "_valid__customer_id": [True, True, True, True],
            "category": ["A", "B", "A", "C"],
            "currency": ["ARS", "ARS", "USD", "USD"],
        }
    )
    pq.write_table(table, path)
    return path


def test_query_filters_grouping_order_limit_and_invalid_masks(tmp_path):
    result = PandasDataEngine().run_query(
        _parquet(tmp_path),
        QuerySpec(
            measures=[MeasureSpec(alias="revenue", aggregation="sum", field="amount")],
            group_by=[GroupBy(field="category")],
            filters=[FilterClause(field="category", op="in", values=["A", "B", "C"])],
            order_by=[OrderBy(field="revenue", direction="desc")],
            limit=1,
            others_bucket=True,
        ),
    )
    assert result.rows == [{"category": "A", "revenue": 130.0}, {"category": "Otros", "revenue": 50.0}]
    assert result.excluded_rows == {"revenue": 1}


def test_query_time_grains_and_all_filter_operators(tmp_path):
    engine = PandasDataEngine()
    path = _parquet(tmp_path)
    for clause in (
        FilterClause(field="category", op="not_in", values=["C"]),
        FilterClause(field="amount", op="between", values=[30, 100]),
        FilterClause(field="amount", op="gte", values=[50]),
        FilterClause(field="amount", op="lte", values=[50]),
        FilterClause(field="customer_name", op="contains", values=["an"]),
    ):
        result = engine.run_query(path, QuerySpec(measures=[MeasureSpec(alias="rows", aggregation="count")], filters=[clause]))
        assert result.rows[0]["rows"] >= 1
    grouped = engine.run_query(path, QuerySpec(measures=[MeasureSpec(alias="rows", aggregation="count")], group_by=[GroupBy(field="date", grain="month")]))
    assert [row["date__month"] for row in grouped.rows] == ["2025-01", "2025-02"]


def test_all_expr_nodes_metric_refs_safe_ratio_and_fallback(tmp_path):
    path = _parquet(tmp_path)
    registry = MetricRegistry()
    definitions = (
        MetricDefinition(id="sum", label_key="sum", description_key="sum.d", group="g", expr=Sum(Field("amount")), output=OutputSpec(type="number")),
        MetricDefinition(id="mean", label_key="mean", description_key="mean.d", group="g", expr=Mean(Field("amount")), output=OutputSpec(type="number")),
        MetricDefinition(id="distinct", label_key="distinct", description_key="distinct.d", group="g", expr=CountDistinct(AnyOf("customer_id", "customer_name")), output=OutputSpec(type="integer")),
        MetricDefinition(id="min", label_key="min", description_key="min.d", group="g", expr=Min(Field("amount")), output=OutputSpec(type="number")),
        MetricDefinition(id="max", label_key="max", description_key="max.d", group="g", expr=Max(Field("amount")), output=OutputSpec(type="number")),
        MetricDefinition(id="mul", label_key="mul", description_key="mul.d", group="g", expr=Sum(RowMul(Field("amount"), Field("quantity"))), output=OutputSpec(type="number")),
        MetricDefinition(id="sub", label_key="sub", description_key="sub.d", group="g", expr=Sub(MetricRef("sum"), Min(Field("amount"))), output=OutputSpec(type="number")),
        MetricDefinition(id="zero", label_key="zero", description_key="zero.d", group="g", expr=Ratio(Count(), Sub(Count(), Count())), output=OutputSpec(type="number")),
        MetricDefinition(id="fallback", label_key="fallback", description_key="fallback.d", group="g", expr=CountDistinct(Field("missing"), fallback=Count()), output=OutputSpec(type="integer")),
    )
    for definition in definitions:
        registry.register(definition)
    metric_engine = MetricEngine(PandasDataEngine(), registry)
    fields = {"amount", "quantity", "customer_name", "category", "currency", "date", "transaction_id"}
    assert metric_engine.evaluate(path, "sum", fields).value == 180.0
    assert metric_engine.evaluate(path, "mean", fields).value == 60.0
    assert metric_engine.evaluate(path, "distinct", fields).value == 3
    assert metric_engine.evaluate(path, "min", fields).value == 30.0
    assert metric_engine.evaluate(path, "max", fields).value == 100.0
    assert metric_engine.evaluate(path, "mul", fields).value == 340.0
    assert metric_engine.evaluate(path, "sub", fields).value == 150.0
    assert metric_engine.evaluate(path, "zero", fields).value is None
    fallback = metric_engine.evaluate(path, "fallback", fields)
    assert fallback.value == 4 and fallback.warnings[0].code == "COUNT_FALLBACK"
    assert registry.requirements("sub") == {"amount"}
    assert registry.get("sub").requires == {"amount"}
    assert registry.requirement_options("distinct") == (frozenset({"customer_id", "customer_name"}),)


def test_universal_availability_filters_exclusions_and_mixed_currency(tmp_path):
    path = _parquet(tmp_path)
    registry = build_universal_registry()
    metric_engine = MetricEngine(PandasDataEngine(), registry)
    fields = {"date", "amount", "quantity", "transaction_id", "customer_name", "currency", "category"}
    availability = resolve_availability(registry, fields)
    assert availability["customers"].available
    assert metric_engine.evaluate(path, "revenue", fields).warnings[0].code == "MIXED_CURRENCY"
    result = metric_engine.evaluate(path, "revenue", fields, [FilterClause(field="currency", op="in", values=["ARS"])])
    assert result.value == 150.0 and result.excluded_rows == 0
    filtered_ratio = metric_engine.evaluate(path, "avg_transaction_value", fields, [FilterClause(field="currency", op="in", values=["ARS"])])
    assert filtered_ratio.value == 75.0
    assert metric_engine.evaluate(path, "transactions", fields).value == 4
    assert metric_engine.evaluate(path, "customers", fields).value == 3
    assert metric_engine.evaluate(path, "customers", (fields - {"customer_name"}) | {"customer_id"}).value == 3
    transaction_fallback = metric_engine.evaluate(path, "transactions", fields - {"transaction_id"})
    assert transaction_fallback.value == 4 and transaction_fallback.warnings[0].code == "COUNT_FALLBACK"
    assert metric_engine.evaluate(path, "quantity", fields).value == 10.0
    assert metric_engine.evaluate(path, "avg_unit_price", fields, [FilterClause(field="currency", op="in", values=["ARS"])]).value == 50.0


def test_comparison_thresholds_previous_zero_and_ranges():
    resolver = ComparisonResolver()
    current = DateRange(from_date=date(2025, 2, 1), to_date=date(2025, 2, 28))
    full = resolver.resolve("previous_month", current, PandasDataEngineCoverage(date(2025, 1, 1), date(2025, 1, 31)), 20, 10, today=date(2025, 3, 1))
    assert full.status == "ok" and full.delta_pct == 1.0
    partial = resolver.resolve("previous_month", current, PandasDataEngineCoverage(date(2025, 1, 1), date(2025, 1, 15)), 20, 10)
    assert partial.status == "ok" and partial.warnings[0].code == "PARTIAL_PREVIOUS_PERIOD"
    insufficient = resolver.resolve("previous_month", current, PandasDataEngineCoverage(date(2025, 1, 1), date(2025, 1, 5)), 20, 10)
    assert insufficient.status == "insufficient_data"
    zero = resolver.resolve("previous_period", current, PandasDataEngineCoverage(date(2025, 1, 1), date(2025, 1, 31)), 20, 0)
    assert zero.status == "previous_zero" and zero.delta_pct is None
    previous_year = resolver.previous_range("previous_year", current)
    assert previous_year == DateRange(from_date=date(2024, 1, 1), to_date=date(2024, 12, 31))
    partial_period = resolver.resolve("previous_period", current, PandasDataEngineCoverage(date(2025, 1, 1), date(2025, 1, 31)), 20, 10, today=date(2025, 2, 15))
    assert partial_period.partial_period


def test_same_universal_registry_resolves_for_all_industry_profiles():
    from bi.profiles.hospitality.profile import PROFILE as hospitality
    from bi.profiles.retail_ecommerce.profile import PROFILE as retail
    from bi.profiles.services.profile import PROFILE as services

    registry = build_universal_registry()
    for profile in (retail, services, hospitality):
        fields = {rule.field_id for rule in profile.data.fields}
        resolved = resolve_availability(registry, fields)
        assert set(resolved) == {metric.id for metric in registry.all()}
        assert resolved["revenue"].available


def PandasDataEngineCoverage(minimum, maximum):
    from analytics_core.engine.query import DateCoverage

    return DateCoverage(minimum=minimum, maximum=maximum)
