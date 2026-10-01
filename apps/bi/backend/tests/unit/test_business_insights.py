from datetime import date
import json
import pytest
from analytics_core.engine.query import DateCoverage, FilterClause
from bi.insights.business import business_insights
from bi.insights.engine import InsightEngine
from bi.metrics.comparison import ComparisonResolver
from bi.metrics.models import DateRange, MetricResult
from bi.profiles import get_profile
from bi.profiles.metrics import build_profile_registry
from test_automatic_comparisons import build


def facts(profile="retail_ecommerce", current=(120.,80.), previous=(50.,50.), metric="revenue"):
    p = get_profile(profile)
    registry = build_profile_registry(p, [])
    definition = registry.get(metric)
    coverage = DateCoverage(minimum=date(2025,1,1), maximum=date(2025,2,28))
    period = DateRange(from_date=date(2025,2,1), to_date=date(2025,2,28))
    resolver = ComparisonResolver()
    comparison = resolver.resolve("previous_period", period, coverage, sum(current), sum(previous))
    result = MetricResult(metric_id=metric, label_key=definition.label_key, status="ok", value=sum(current), format=definition.output, comparison=comparison)
    segments = {name: resolver.resolve("previous_period",period,coverage,a,b) for name,a,b in zip(("A","B"),current,previous)}
    grouped = {(metric,"concept"): (dict(zip(("A","B"),current)),dict(zip(("A","B"),previous)),segments)}
    return business_insights(p,registry,[result],grouped,[])


@pytest.mark.parametrize("current,word",[((120.,80.),"aumentó"),((20.,30.),"disminuyó")])
def test_growth_decline_neutral_structured(current,word):
    item = next(i for i in facts(current=current) if i.kind=="change")
    assert word in item.text and item.severity=="neutral"
    assert item.params["baseline"]==100 and item.params["period"]["previous_range"]
    assert not any(term in item.text for term in ("gracias", "culpa", "deberías", "porque", "significativo"))


def test_leadership_concentration_segment_and_signed_contributions():
    items=facts(current=(180.,20.),previous=(50.,100.))
    assert any(i.kind=="concentration" and i.params["share"]==.9 for i in items)
    assert any(i.kind=="segment_change" for i in items)
    contribution=[i for i in items if i.kind=="contribution"]
    assert sorted(i.params["contribution"] for i in contribution)==[-1.6,2.6]
    assert sum(i.params["segment_delta"] for i in contribution)==50
    assert any(i.kind=="leadership" for i in facts(current=(55.,45.)))


@pytest.mark.parametrize("current,previous",[((50.,50.),(50.,50.)), ((-10.,-20.),(-20.,-10.))])
def test_zero_change_and_ties_no_fake_leader(current,previous):
    items=facts(current=current,previous=previous)
    assert not any(i.kind=="contribution" for i in items)
    if current[0]==current[1]: assert not any(i.kind in {"leadership","concentration"} for i in items)
    json.dumps([i.model_dump() for i in items],allow_nan=False)


def test_zero_baseline_absolute_only():
    item=next(i for i in facts(previous=(0.,0.)) if i.kind=="change")
    assert item.params["relative_delta"] is None and "%" not in item.text


def test_nonadditive_never_contributes():
    assert not any(i.kind in {"contribution", "concentration"} for i in facts(metric="avg_transaction_value"))


@pytest.mark.parametrize("profile,word",[("retail_ecommerce","Venta"),("services","Facturación"),("hospitality","Ingreso"),("custom","Importe")])
def test_profile_terminology(profile,word):
    assert any(i.text.startswith(word) for i in facts(profile=profile))


def test_real_filters_history_currency_and_margin(tmp_path):
    filters=[FilterClause(field="date",op="between",values=["2025-02-01","2025-02-28"]),FilterClause(field="category",op="in",values=["A"])]
    data=build(tmp_path,categories=("A","B","A","B"),filters=filters)
    items=data["insights_top"]["insights"]
    assert all(i["params"]["filters"][-1]["values"]==["A"] for i in items)
    revenue=next(i for i in items if i["metric_id"]=="revenue")
    assert revenue["params"]["current"]==60 and revenue["params"]["baseline"]==50
    data=build(tmp_path,currencies=("ARS","USD","ARS","USD"))
    assert not any(i["metric_id"]=="revenue" for i in data["insights_top"]["insights"])
    data=build(tmp_path,mode="none")
    assert not any(i["kind"] in {"change","contribution","segment_change","divergence"} for i in data["insights_top"]["insights"])


def test_prioritization_deterministic_and_deduplicated():
    items=facts()
    engine=InsightEngine()
    assert engine.prioritize(items+items,3)==engine.prioritize(list(reversed(items)),3)
    assert len(engine.prioritize(items,3))<=3


def test_top_n_complete_partition_and_small_segments():
    p=get_profile("custom"); registry=build_profile_registry(p,[])
    result=MetricResult(metric_id="revenue",label_key="metric.revenue",status="ok",value=100,format=registry.get("revenue").output)
    current={"A":40.,"B":30.,"C":20.,"D":10.}
    items=business_insights(p,registry,[result],{("revenue","concept"):(current,None,{})},[])
    assert any(i.params.get("top_n")==3 and i.params["share"]==.9 for i in items)
    assert not any(i.params.get("top_n") for i in facts())
    items=facts(current=(199.,1.),previous=(99.,1.))
    assert not any(i.params.get("segment")=="B" and i.kind in {"contribution","segment_change"} for i in items)


def test_divergence_valid_and_percent_delta(tmp_path):
    # Revenue increases, gross margin decreases with the same complete population.
    # Existing helper costs lead to an increased margin; use a standalone valid pair.
    p=get_profile("retail_ecommerce");registry=build_profile_registry(p,[])
    from bi.metrics.models import ComparisonResult, OutputSpec
    comp=ComparisonResult(mode="previous_period",status="ok",previous_value=100,delta_abs=20,delta_pct=.2)
    margin=comp.model_copy(update={"previous_value":.4,"delta_abs":-.03,"delta_pct":None,"delta_pp":-3.})
    revenue=MetricResult(metric_id="revenue",label_key="metric.revenue",status="ok",value=120,format=OutputSpec(type="currency"),comparison=comp)
    ratio=MetricResult(metric_id="gross_margin_pct",label_key="metric.gross_margin_pct",status="ok",value=.37,format=OutputSpec(type="percent"),comparison=margin)
    found=business_insights(p,registry,[revenue,ratio],{},[])
    assert any(i.kind=="divergence" and "3,0 pp" in i.text for i in found)
    assert not any(i.kind=="contribution" for i in found)
    assert not any(i.kind=="divergence" for i in business_insights(p,registry,[revenue,ratio.model_copy(update={"excluded_rows":1})],{},[]))


def test_nulls_and_nonfinite_no_claims():
    p=get_profile("custom");registry=build_profile_registry(p,[])
    result=MetricResult(metric_id="revenue",label_key="metric.revenue",status="ok",value=100,format=registry.get("revenue").output)
    found=business_insights(p,registry,[result],{("revenue","concept"):({None:80.,"A":20.},None,{})},[])
    assert not found
    assert not business_insights(p,registry,[result.model_copy(update={"value":float("nan")})],{},[])


def test_null_negative_group_never_inflates_share():
    p=get_profile("custom");registry=build_profile_registry(p,[])
    result=MetricResult(metric_id="revenue",label_key="metric.revenue",status="ok",value=40,format=registry.get("revenue").output)
    found=business_insights(p,registry,[result],{("revenue","concept"):({None:-80.,"A":100.,"B":20.},None,{})},[])
    assert not any(i.kind=="concentration" or i.params["share"] is not None for i in found)
