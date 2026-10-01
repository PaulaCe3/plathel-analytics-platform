from calendar import monthrange
from datetime import date, datetime

import pyarrow as pa
import pyarrow.parquet as pq
import pytest

from analytics_core.engine.pandas_impl.engine import PandasDataEngine
from analytics_core.engine.query import FilterClause
from analytics_core.quality.models import QualitySummary
from bi.dashboard.builder import DashboardBuilder
from bi.insights.anomalies import anomaly_candidates
from bi.insights.engine import Insight, InsightEngine
from bi.metrics.models import ComparisonSpec
from bi.profiles import get_profile
from bi.profiles.metrics import build_profile_registry
from bi.profiles.registry import profile_fields


def points(values):
    return [[f"2024-{index:02d}", value] for index, value in enumerate(values, 1)]


def detect(values, *, profile="retail_ecommerce", analysis_end=date(2024, 12, 31)):
    return anomaly_candidates(get_profile(profile), "revenue", "Facturación", points(values),
                              "month", analysis_end, [{"field": "category", "values": ["A"]}],
                              today=date(2026, 1, 1))


@pytest.mark.parametrize("value,kind,word", [(180, "anomaly_high", "alto"), (20, "anomaly_low", "bajo")])
def test_robust_high_and_low_anomaly(value, kind, word):
    found = detect([100, 101, 99, 102, 98, 100, 101, 99, 100, 102, 98, value])
    assert len(found) == 1 and found[0].kind == kind
    assert found[0].params["observed"] == value and found[0].params["baseline"] == 100
    assert found[0].params["latest"] is True and found[0].params["filters"][0]["values"] == ["A"]
    assert word in found[0].text and "patrón histórico observado" in found[0].text
    assert not any(term in found[0].text for term in ("porque", "significativo", "crítico", "deberías", "problema"))


def test_normal_short_constant_and_invalid_series_are_silent():
    assert not detect([98, 101, 99, 102, 100, 97, 103, 100, 99, 101, 98, 102])
    assert not anomaly_candidates(get_profile("custom"), "revenue", "Importe", points([1] * 7), "month", date(2024, 12, 31), [], today=date(2026, 1, 1))
    assert not detect([10] * 12)
    invalid = points([10] * 12); invalid[3][1] = None
    assert not anomaly_candidates(get_profile("custom"), "revenue", "Importe", invalid, "month", date(2024, 12, 31), [], today=date(2026, 1, 1))


def test_mad_zero_uses_only_valid_robust_fallback():
    found = detect([10, 10, 10, 10, 10, 10, 10, 11, 12, 13, 14, 100])
    assert found and found[0].params["technical"]["method"] == "iqr"
    assert not detect([10, 10, 10, 10, 10, 10, 10, 100, 10, 10, 10, 10])


def test_incomplete_and_missing_periods_are_not_evaluated():
    values = [100, 101, 99, 102, 98, 100, 101, 99, 100, 102, 98, 300]
    assert not detect(values, analysis_end=date(2024, 12, 15))
    missing = points(values); missing.pop(4)
    assert not anomaly_candidates(get_profile("custom"), "revenue", "Importe", missing, "month", date(2024, 12, 31), [], today=date(2026, 1, 1))


def test_negative_values_and_multiple_outliers_remain_finite_and_prioritized():
    negative = detect([-100, -101, -99, -102, -98, -100, -101, -99, -100, -102, -98, -180])
    assert negative and negative[0].kind == "anomaly_low"
    multiple = detect([200, 101, 99, 102, 98, 100, 101, 99, 100, 102, 98, 300])
    assert len(multiple) == 1 and multiple[0].params["period"] == "2024-12"
    assert all(isinstance(multiple[0].params[key], (int, float)) for key in ("observed", "baseline", "deviation"))


@pytest.mark.parametrize("profile,label", [("retail_ecommerce", "Venta"), ("services", "Facturación"),
                                             ("hospitality", "Ingreso"), ("custom", "Importe")])
def test_multi_industry_terminology(profile, label):
    item = anomaly_candidates(get_profile(profile), "revenue", label,
        points([100, 101, 99, 102, 98, 100, 101, 99, 100, 102, 98, 200]),
        "month", date(2024, 12, 31), [], today=date(2026, 1, 1))[0]
    assert label.lower() in item.text


def _dashboard(tmp_path, category_filter, currencies=None):
    dates = [datetime(2024, month, monthrange(2024, month)[1]) for month in range(1, 13)]
    table = {"date": dates * 2, "amount": [100, 101, 99, 102, 98, 100, 101, 99, 100, 102, 98, 300] + [50] * 12,
             "category": ["A"] * 12 + ["B"] * 12, "channel": ["Online"] * 24,
             "transaction_id": [str(index) for index in range(24)], "currency": currencies or ["ARS"] * 24}
    path = tmp_path / "canonical.parquet"; pq.write_table(pa.table(table), path)
    profile = get_profile("retail_ecommerce")
    builder = DashboardBuilder(PandasDataEngine(), build_profile_registry(profile, []))
    data = builder.build(profile=profile, canonical_path=path, fields=profile_fields(profile),
        available=set(table), filters=[FilterClause(field="category", op="in", values=[category_filter])],
        comparison=ComparisonSpec(mode="none"), time_field="date", grain="auto",
        quality=QualitySummary(), row_count=24)[1]
    return data["insights_top"]["insights"]


def test_dashboard_anomalies_use_active_filter_and_mixed_currency_guard(tmp_path):
    assert any(item["kind"] == "anomaly_high" for item in _dashboard(tmp_path, "A"))
    assert not any(item["kind"].startswith("anomaly") for item in _dashboard(tmp_path, "B"))
    currencies = ["ARS", "USD"] * 12
    assert not any(item["metric_id"] == "revenue" and item["kind"].startswith("anomaly")
                   for item in _dashboard(tmp_path, "A", currencies))


def test_latest_anomaly_deduplicates_change_and_shares_three_item_limit():
    anomaly = Insight(id="a", rule_id="anomaly_high", kind="anomaly_high", severity="attention",
        template_key="business.fact", params={"latest": True}, text="inusualmente alto", metric_id="revenue", score=1.2)
    change = Insight(id="c", rule_id="change", kind="change", severity="neutral",
        template_key="business.fact", params={}, text="aumentó", metric_id="revenue", score=.9)
    other = [Insight(id=str(index), rule_id="leadership", kind="leadership", severity="neutral",
        template_key="business.fact", params={"segment": str(index)}, text="líder", metric_id="transactions",
        dimension="category", score=.8-index/10) for index in range(4)]
    result = InsightEngine().prioritize([change, anomaly, *other], limit=3)
    assert anomaly in result and change not in result and len(result) == 3
