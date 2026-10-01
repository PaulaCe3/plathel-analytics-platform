from bi.insights.engine import Insight, InsightEngine
from bi.insights.rules.universal import channel_dominance, data_quality_alert, leader_share, peak_period, top_n_concentration
from datetime import datetime
import pyarrow as pa
import pyarrow.parquet as pq

from analytics_core.engine.pandas_impl.engine import PandasDataEngine
from analytics_core.canonical.fields import FieldSpec
from analytics_core.quality.models import QualitySummary
from bi.dashboard.builder import DashboardBuilder
from bi.metrics.models import ComparisonSpec
from bi.metrics.universal import build_universal_registry
from bi.profiles.custom.profile import PROFILE as CUSTOM
from bi.profiles.hospitality.profile import PROFILE as HOSPITALITY
from bi.profiles.registry import profile_fields
from bi.profiles.retail_ecommerce.profile import PROFILE as RETAIL
from bi.profiles.services.profile import PROFILE as SERVICES


def test_universal_insight_guards_and_rules():
    assert not leader_share([["A", 9, .9], ["B", 1, .1]], "category")
    assert leader_share([["A", 6, .6], ["B", 3, .3], ["C", 1, .1]], "category")
    assert not top_n_concentration([[str(i), 1, .1] for i in range(10)], "customer")
    assert top_n_concentration([[str(i), 1, .05] for i in range(20)], "customer")
    assert peak_period([["Jan", 1], ["Feb", 4], ["Mar", 2], ["Apr", 3]])[0].params["period"] == "Feb"
    assert channel_dominance([["Web", 8, .8], ["Store", 2, .2]])
    assert not data_quality_alert(1, 100)
    assert data_quality_alert(10, 100)


def test_insight_engine_deduplicates_orders_and_limits():
    items = [Insight(id=f"i{i}", rule_id="same" if i < 2 else f"r{i}", severity="neutral", template_key="k", params={}, text="k", dimension="d" if i < 2 else str(i), score=float(i)) for i in range(10)]
    result = InsightEngine().prioritize(items, limit=3)
    assert len(result) == 3 and result[0].score == 9
    assert sum(item.rule_id == "same" for item in result) <= 1


def test_dashboard_builder_uses_same_engine_for_all_profiles(tmp_path):
    path = tmp_path / "canonical.parquet"
    values = {
        "date": [datetime(2025, 1, 1), datetime(2025, 2, 1)], "check_in": [datetime(2025, 1, 1), datetime(2025, 2, 1)], "booking_date": [datetime(2024, 12, 1), datetime(2025, 1, 1)],
        "amount": [100.0, 200.0], "_valid__amount": [True, True], "transaction_id": ["1", "2"], "customer_name": ["A", "B"], "concept": ["X", "Y"],
        "category": ["C1", "C2"], "channel": ["Web", "Store"], "location": ["L1", "L2"], "responsible": ["R1", "R2"], "project": ["P1", "P2"], "room_type": ["Suite", "Twin"], "currency": ["ARS", "ARS"], "custom__segment": ["S1", "S2"],
    }
    pq.write_table(pa.table(values), path)
    builder = DashboardBuilder(PandasDataEngine(), build_universal_registry())
    cases = ((RETAIL, "date", {"date", "amount", "transaction_id", "customer_name", "concept", "category", "channel", "location", "currency"}), (SERVICES, "date", {"date", "amount", "transaction_id", "customer_name", "concept", "responsible", "project", "currency"}), (HOSPITALITY, "check_in", {"check_in", "booking_date", "amount", "transaction_id", "room_type", "channel", "location", "currency"}), (CUSTOM, "date", {"date", "amount", "concept", "custom__segment", "currency"}))
    for profile, time_field, available in cases:
        fields = profile_fields(profile)
        if profile is CUSTOM:
            fields.append(FieldSpec(id="custom__segment", label_key="custom__segment", kind="dimension", dtype="string", scope="custom"))
        spec, data, filtered, _ = builder.build(profile=profile, canonical_path=path, fields=fields, available=available, filters=[], comparison=ComparisonSpec(mode="none"), time_field=time_field, grain="auto", quality=QualitySummary(), row_count=2)
        assert spec.profile_id == profile.id and filtered == 2 and "kpi_revenue" in data
        assert len(spec.key_chart_ids) <= 4
        assert len(spec.key_chart_ids) == len(set(spec.key_chart_ids))
        assert all(data[chart_id].status == "ok" for chart_id in spec.key_chart_ids)
        assert all(data[chart_id].meta["dimension"] in available for chart_id in spec.key_chart_ids)
    assert any(section.id == "custom_dimensions" for section in spec.sections)
