from datetime import datetime
import math
import pytest
import pyarrow as pa
import pyarrow.parquet as pq
from analytics_core.engine.pandas_impl.engine import PandasDataEngine
from analytics_core.engine.query import FilterClause
from analytics_core.mapping.models import ColumnMapping
from analytics_core.canonical.fields import FieldSpec, UNIVERSAL_FIELDS
from analytics_core.quality.models import QualitySummary
from bi.dashboard.builder import DashboardBuilder
from bi.dashboard.templates import WidgetTemplate
from bi.metrics.availability import resolve_availability
from bi.metrics.engine import MetricEngine
from bi.metrics.models import ComparisonSpec
from bi.profiles import get_profile, list_profiles
from bi.profiles.metrics import build_profile_registry
from bi.profiles.registry import profile_fields


def mappings(cost="total", discount="amount"):
    return [ColumnMapping(column_key="c1", target_field="cost", disposition="canonical", options={"basis": cost}), ColumnMapping(column_key="c2", target_field="discount", disposition="canonical", options={"kind": discount})]


@pytest.fixture
def dataset(tmp_path):
    data = {"date": [datetime(2025, 1, 1), datetime(2025, 1, 31), datetime(2025, 2, 1), datetime(2025, 2, 28)], "check_in": [datetime(2025, 1, 1), datetime(2025, 1, 31), datetime(2025, 2, 1), datetime(2025, 2, 28)], "amount": [100., 200., 300., 400.], "cost": [40., 80., 120., 160.], "discount": [10., 20., 30., 40.], "quantity": [1., 2., 3., 4.], "duration_hours": [2., 4., 6., 8.], "nights": [1., 2., 3., 4.], "transaction_id": ["a", "a", "b", "c"], "category": ["A", "B", "C", "C"], "concept": ["A", "B", "C", "C"], "responsible": ["A", "B", "C", "C"], "project": ["A", "B", "C", "C"], "room_type": ["A", "B", "C", "C"], "channel": ["A", "B", "C", "C"], "currency": ["ARS"] * 4}
    for field in ("date", "check_in", "amount", "cost", "discount", "quantity", "duration_hours", "nights", "transaction_id"):
        data[f"_valid__{field}"] = [True] * 4
    path = tmp_path / "canonical.parquet"
    pq.write_table(pa.table(data), path)
    return path, data


def evaluate(dataset, profile, metric, filters=(), available=None):
    path, data = dataset
    registry = build_profile_registry(get_profile(profile), mappings())
    return MetricEngine(PandasDataEngine(), registry).evaluate(path, metric, set(data) if available is None else available, list(filters))


@pytest.mark.parametrize("profile,metric,expected", [("retail_ecommerce", "units_sold", 10), ("retail_ecommerce", "total_cost", 400), ("retail_ecommerce", "gross_profit", 600), ("retail_ecommerce", "gross_margin_pct", .6), ("retail_ecommerce", "average_discount", 25), ("services", "service_hours", 20), ("services", "revenue_per_hour", 50), ("hospitality", "total_nights", 10), ("hospitality", "adr", 100), ("hospitality", "average_stay", 2.5), ("custom", "revenue", 1000), ("custom", "transactions", 3)])
def test_registered_metrics(dataset, profile, metric, expected):
    result = evaluate(dataset, profile, metric)
    assert result.status == "ok" and result.value == pytest.approx(expected)
    assert result.excluded_rows == 0


@pytest.mark.parametrize("profile,metric,field", [("retail_ecommerce", "gross_profit", "cost"), ("retail_ecommerce", "gross_margin_pct", "cost"), ("services", "revenue_per_hour", "duration_hours"), ("hospitality", "adr", "nights"), ("hospitality", "average_stay", "nights")])
def test_missing_fields(dataset, profile, metric, field):
    registry = build_profile_registry(get_profile(profile), mappings())
    available = set(dataset[1]) - {field}
    status = resolve_availability(registry, available)[metric]
    assert not status.available and status.missing_fields == [field]
    result = evaluate(dataset, profile, metric, available=available)
    assert result.status == "unavailable" and result.value is None


@pytest.mark.parametrize("profile,metric,field,expected", [("retail_ecommerce", "gross_profit", "cost", 420), ("retail_ecommerce", "gross_margin_pct", "cost", .6), ("services", "revenue_per_hour", "duration_hours", 50), ("hospitality", "adr", "nights", 100)])
def test_invalid_union_population(dataset, profile, metric, field, expected):
    path, data = dataset
    data["_valid__amount"][0] = False
    data[f"_valid__{field}"][1] = False
    pq.write_table(pa.table(data), path)
    result = evaluate(dataset, profile, metric)
    assert result.value == pytest.approx(expected) and result.excluded_rows == 2


@pytest.mark.parametrize("profile,metric,field", [("retail_ecommerce", "gross_margin_pct", "amount"), ("services", "revenue_per_hour", "duration_hours"), ("hospitality", "adr", "nights")])
def test_zero_denominators(dataset, profile, metric, field):
    path, data = dataset
    data[field] = [0.] * 4
    pq.write_table(pa.table(data), path)
    result = evaluate(dataset, profile, metric)
    assert result.status == "empty" and result.value is None


@pytest.mark.parametrize("profile,metric", [("retail_ecommerce", "gross_profit"), ("retail_ecommerce", "gross_margin_pct"), ("retail_ecommerce", "average_discount"), ("services", "revenue_per_hour"), ("hospitality", "adr")])
def test_mixed_currency_and_filtered_currency(dataset, profile, metric):
    path, data = dataset
    data["currency"][0] = "USD"
    pq.write_table(pa.table(data), path)
    result = evaluate(dataset, profile, metric)
    assert result.status == "unavailable" and result.warnings[0].code == "MIXED_CURRENCY"
    assert evaluate(dataset, profile, metric, [FilterClause(field="currency", op="in", values=["ARS"])]).status == "ok"


@pytest.mark.parametrize("profile,metric,dimension,expected", [("retail_ecommerce", "gross_profit", "category", 420), ("services", "service_hours", "responsible", 14), ("services", "revenue_per_hour", "project", 50), ("hospitality", "total_nights", "room_type", 7), ("hospitality", "adr", "channel", 100)])
def test_industry_filters(dataset, profile, metric, dimension, expected):
    assert evaluate(dataset, profile, metric, [FilterClause(field=dimension, op="in", values=["C"])]).value == pytest.approx(expected)


@pytest.mark.parametrize("profile_id,metric,previous,current", [("retail_ecommerce", "gross_profit", 180, 420), ("services", "service_hours", 6, 14), ("services", "revenue_per_hour", 50, 50), ("hospitality", "adr", 100, 100)])
def test_dashboard_comparison_and_specific_charts(dataset, profile_id, metric, previous, current):
    path, data = dataset
    profile = get_profile(profile_id)
    registry = build_profile_registry(profile, mappings())
    builder = DashboardBuilder(PandasDataEngine(), registry)
    time = profile.data.primary_date
    spec, values, count, _ = builder.build(profile=profile, canonical_path=path, fields=profile_fields(profile), available=set(data), filters=[FilterClause(field=time, op="between", values=["2025-02-01", "2025-02-28"])], comparison=ComparisonSpec(mode="previous_month"), time_field=time, grain="month", quality=QualitySummary(), row_count=4)
    kpi = values[f"kpi_{metric}"]
    assert kpi.value == pytest.approx(current)
    assert kpi.comparison.status == "ok" and kpi.comparison.previous_value == pytest.approx(previous)
    assert count == 2 and any(section.id == "industry_specific" for section in spec.sections)
    assert all(getattr(value, "status", None) != "error" for value in values.values())
    for widget in profile.bi.widgets:
        chart = values[widget.id]
        assert chart.series[0].key == widget.metric_id
        filtered = evaluate(dataset, profile_id, widget.metric_id, [FilterClause(field=time, op="between", values=["2025-02-01", "2025-02-28"]), FilterClause(field=widget.dimension, op="in", values=["C"])])
        assert chart.series[0].points[0][1] == pytest.approx(filtered.value)


def test_semantics_explicit_and_unambiguous_only(dataset):
    profile = get_profile("retail_ecommerce")
    for selected in ([], mappings(cost="unit", discount="percent")):
        registry = build_profile_registry(profile, selected)
        status = resolve_availability(registry, set(dataset[1]))
        for metric in ("total_cost", "gross_profit", "gross_margin_pct", "average_discount"):
            assert not status[metric].available and status[metric].reason_key
    registry = build_profile_registry(profile, mappings())
    assert all(value.available for value in resolve_availability(registry, set(dataset[1])).values() if not value.missing_fields)


def test_profiles_contracts_and_custom_isolation(dataset):
    for profile in list_profiles():
        registry = build_profile_registry(profile, mappings())
        fields = {field.id for field in profile_fields(profile)} | {field.id for field in UNIVERSAL_FIELDS}
        assert set(profile.bi.metrics) == {metric.id for metric in registry.all()}
        for metric in registry.all():
            assert metric.label_key and metric.description_key and metric.group
            assert metric.requires == registry.requirements(metric.id)
            assert all(options & fields for options in registry.requirement_options(metric.id))
            assert math.isfinite(evaluate(dataset, profile.id, metric.id).value or 0)
        assert set(profile.bi.kpi_order) <= set(profile.bi.metrics)
        assert all(widget.metric_id in profile.bi.metrics and widget.dimension in fields for widget in profile.bi.widgets)
    registry = build_profile_registry(get_profile("custom"))
    assert len(registry.all()) == 6
    path, data = dataset
    data["custom__segment"] = ["A", "B", "C", "C"]
    data["custom__budget"] = [1., 2., 3., 4.]
    pq.write_table(pa.table(data), path)
    profile = get_profile("custom")
    fields = profile_fields(profile) + [FieldSpec(id="custom__segment", label_key="segment", kind="dimension", dtype="string", scope="custom"), FieldSpec(id="custom__budget", label_key="budget", kind="measure", dtype="decimal", scope="custom")]
    spec, values, _, _ = DashboardBuilder(PandasDataEngine(), registry).build(profile=profile, canonical_path=path, fields=fields, available=set(data), filters=[], comparison=ComparisonSpec(), time_field="date", grain="month", quality=QualitySummary(), row_count=4)
    assert "revenue_by_custom__segment" in values
    assert "revenue_by_custom__budget" not in values
    assert not any(section.id == "industry_specific" for section in spec.sections)
    assert all(item.metric_id in profile.bi.metrics for item in spec.unavailable_metrics)


@pytest.mark.parametrize("profile_id,dimension", [("retail_ecommerce", "category"), ("services", "responsible"), ("hospitality", "room_type")])
def test_industry_insight_thresholds_and_filters(dataset, profile_id, dimension):
    path, data = dataset
    profile = get_profile(profile_id)
    builder = DashboardBuilder(PandasDataEngine(), build_profile_registry(profile, mappings()))
    def build(filters):
        return builder.build(profile=profile, canonical_path=path, fields=profile_fields(profile), available=set(data), filters=filters, comparison=ComparisonSpec(), time_field=profile.data.primary_date, grain="month", quality=QualitySummary(), row_count=4)[1]["insights_top"]["insights"]
    insights = build([])
    specific = [item for item in insights if item["rule_id"] == "industry_leader"]
    assert specific and specific[0]["dimension"] == dimension and specific[0]["params"]["value"] == "C"
    assert not any(item["rule_id"] == "industry_leader" for item in build([FilterClause(field=dimension, op="in", values=["C"])]))


def test_nonadditive_others_recomputed(dataset):
    path, data = dataset
    builder = DashboardBuilder(PandasDataEngine(), build_profile_registry(get_profile("services")))
    chart = builder._widget(WidgetTemplate(id="ratio", type="breakdown", title_key="metric.revenue_per_hour", metric_id="revenue_per_hour", dimension="project", top_n=1), path, set(data), [], "date", "month", QualitySummary())
    assert chart.series[0].points == [["A", 50., None], ["Otros", 50., None]]


@pytest.mark.parametrize("profile,metric,field", [("services", "service_hours", "duration_hours"), ("hospitality", "total_nights", "nights"), ("hospitality", "average_stay", "nights"), ("retail_ecommerce", "total_cost", "cost")])
def test_single_field_invalid_and_empty(dataset, profile, metric, field):
    path, data = dataset
    data[f"_valid__{field}"] = [False] * 4
    pq.write_table(pa.table(data), path)
    result = evaluate(dataset, profile, metric)
    assert result.value is None and result.status == "empty" and result.excluded_rows == 4


def test_mixed_currency_with_blank_group_cannot_hide_second_currency(dataset):
    path, data = dataset
    data["currency"] = [None, "ARS", "USD", "USD"]
    pq.write_table(pa.table(data), path)
    assert evaluate(dataset, "hospitality", "adr").status == "unavailable"
    filtered = evaluate(dataset, "hospitality", "adr", [FilterClause(field="currency", op="in", values=["USD"])])
    assert filtered.format.currency == "USD"


def test_zero_revenue_dashboard_has_no_false_leader(dataset):
    path, data = dataset
    data["amount"] = [0.] * 4
    pq.write_table(pa.table(data), path)
    profile = get_profile("retail_ecommerce")
    _, values, _, _ = DashboardBuilder(PandasDataEngine(), build_profile_registry(profile, mappings())).build(profile=profile, canonical_path=path, fields=profile_fields(profile), available=set(data), filters=[], comparison=ComparisonSpec(), time_field="date", grain="month", quality=QualitySummary(), row_count=4)
    assert values["kpi_gross_margin_pct"].value is None
    assert not any(item["rule_id"] == "industry_leader" for item in values["insights_top"]["insights"])


@pytest.mark.parametrize("grain", ["day", "week", "month", "quarter", "year"])
def test_specific_timeseries_reuses_metrics_and_skips_invalid_dates(dataset, grain):
    path, data = dataset
    data["date"][0] = None
    data["_valid__date"][0] = False
    pq.write_table(pa.table(data), path)
    builder = DashboardBuilder(PandasDataEngine(), build_profile_registry(get_profile("services")))
    result = builder._widget(WidgetTemplate(id="hours", type="timeseries", title_key="metric.service_hours", metric_id="service_hours"), path, set(data), [], "date", grain, QualitySummary())
    assert result.status == "ok"
    assert sum(point[1] for point in result.series[0].points) == 18
