from datetime import datetime

import pyarrow as pa
import pyarrow.parquet as pq
import pytest

from analytics_core.engine.pandas_impl.engine import PandasDataEngine
from analytics_core.engine.query import FilterClause
from analytics_core.mapping.models import ColumnMapping
from bi.dashboard.builder import DashboardBuilder
from bi.dashboard.widgets import SegmentComparisonSpec
from bi.profiles import get_profile
from bi.profiles.metrics import build_profile_registry
from bi.profiles.registry import profile_fields


def comparison(tmp_path, profile_id="retail_ecommerce", *, filters=(), currencies=None):
    profile = get_profile(profile_id)
    data = {
        "date": [datetime(2025, 1, 1)] * 6, "check_in": [datetime(2025, 1, 1)] * 6,
        "amount": [100., 40., 60., 30., 999., 999.], "cost": [50., 20., 40., 20., 1., 1.],
        "duration_hours": [2., 1., 3., 2., 1., 1.], "nights": [1., 1., 2., 1., 1., 1.],
        "channel": ["Online", "Online", "Local", "Local", "Online", "Local"],
        "category": ["A", "B", "A", "B", "Z", "Z"],
        "transaction_id": [str(index) for index in range(6)],
        "currency": currencies or ["ARS"] * 6,
    }
    path = tmp_path / f"{profile_id}.parquet"; pq.write_table(pa.table(data), path)
    mappings = [ColumnMapping(column_key="cost", target_field="cost", disposition="canonical", options={"basis": "total"})]
    builder = DashboardBuilder(PandasDataEngine(), build_profile_registry(profile, mappings))
    result = builder.compare(profile=profile, canonical_path=path, available=set(data), fields=profile_fields(profile),
        filters=list(filters), selection=SegmentComparisonSpec(dimension="channel", value_a="Online", value_b="Local"))
    return result


def test_comparison_ignores_own_dimension_filter_and_keeps_other_filters(tmp_path):
    result = comparison(tmp_path, filters=[FilterClause(field="channel", op="in", values=["Online"]),
        FilterClause(field="category", op="in", values=["A"])])
    assert result.status == "ok" and result.value_a == "Online" and result.value_b == "Local"
    metrics = {item.metric_id: item for item in result.metrics}
    assert metrics["revenue"].value_a == 100 and metrics["revenue"].value_b == 60
    assert metrics["transactions"].value_a == metrics["transactions"].value_b == 1
    assert metrics["avg_transaction_value"].value_a == 100 and metrics["avg_transaction_value"].value_b == 60


def test_missing_population_and_mixed_currency_are_safe(tmp_path):
    unavailable = comparison(tmp_path, filters=[FilterClause(field="category", op="in", values=["missing"])])
    assert unavailable.status == "unavailable" and not unavailable.metrics
    mixed = comparison(tmp_path, filters=[FilterClause(field="category", op="in", values=["A", "B"])],
        currencies=["ARS", "USD", "ARS", "ARS", "ARS", "ARS"])
    ids = {item.metric_id for item in mixed.metrics}
    assert "revenue" not in ids and "avg_transaction_value" not in ids
    assert "transactions" in ids


@pytest.mark.parametrize("profile,metric", [("retail_ecommerce", "gross_margin_pct"),
    ("services", "revenue_per_hour"), ("hospitality", "adr"), ("custom", "revenue")])
def test_comparison_uses_profile_registry_for_every_industry(tmp_path, profile, metric):
    result = comparison(tmp_path, profile, filters=[FilterClause(field="category", op="in", values=["A"])])
    assert result.status == "ok" and metric in {item.metric_id for item in result.metrics}


def test_unknown_dimension_is_cleanly_unavailable(tmp_path):
    profile = get_profile("custom"); path = tmp_path / "simple.parquet"
    pq.write_table(pa.table({"amount": [1.], "channel": ["A"]}), path)
    result = DashboardBuilder(PandasDataEngine(), build_profile_registry(profile)).compare(
        profile=profile, canonical_path=path, available={"amount", "channel"}, fields=profile_fields(profile),
        filters=[], selection=SegmentComparisonSpec(dimension="missing", value_a="A", value_b="B"))
    assert result.status == "unavailable" and result.reason_key == "comparison.dimension_unavailable"


def test_equal_values_are_rejected():
    with pytest.raises(ValueError):
        SegmentComparisonSpec(dimension="channel", value_a="Online", value_b="Online")
