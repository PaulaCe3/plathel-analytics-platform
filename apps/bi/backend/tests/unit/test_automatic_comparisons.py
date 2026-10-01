from datetime import date, datetime, timezone
import math
import pytest
import pyarrow as pa
import pyarrow.parquet as pq
from analytics_core.engine.pandas_impl.engine import PandasDataEngine
from analytics_core.engine.query import DateCoverage, FilterClause
from analytics_core.mapping.models import ColumnMapping
from analytics_core.quality.models import QualitySummary
from bi.dashboard.builder import DashboardBuilder
from bi.metrics.comparison import ComparisonResolver
from bi.metrics.models import ComparisonSpec, DateRange
from bi.profiles import get_profile
from bi.profiles.metrics import build_profile_registry
from bi.profiles.registry import profile_fields


def build(tmp_path, *, amounts=(50.,50.,60.,60.), currencies=("ARS",)*4, categories=("A",)*4, filters=None, profile_id="retail_ecommerce", dated=True, dates=None, mode="previous_period"):
    dates=dates or [datetime(2025,1,1),datetime(2025,1,31,23,59),datetime(2025,2,1),datetime(2025,2,28,23,59)]
    data={"amount":list(amounts),"cost":[30.,30.,33.,33.],"quantity":[1.,1.,1.,1.],"duration_hours":[1.,1.,1.,1.],"nights":[1.,1.,1.,1.],"category":list(categories),"channel":["Online"]*4,"currency":list(currencies),"transaction_id":["1","2","3","4"]}
    if dated:data.update(date=dates,check_in=dates)
    path=tmp_path/"canonical.parquet";pq.write_table(pa.table(data),path)
    profile=get_profile(profile_id);mapping=[ColumnMapping(column_key="c1",target_field="cost",disposition="canonical",options={"basis":"total"})]
    registry=build_profile_registry(profile,mapping);builder=DashboardBuilder(PandasDataEngine(),registry)
    if filters is None:filters=[FilterClause(field=profile.data.primary_date,op="between",values=["2025-02-01","2025-02-28"])] if dated else []
    return builder.build(profile=profile,canonical_path=path,fields=profile_fields(profile),available=set(data),filters=filters,comparison=ComparisonSpec(mode=mode),time_field=profile.data.primary_date,grain="auto",quality=QualitySummary(),row_count=4)[1]


@pytest.mark.parametrize("current,expected",[(120.,.2),(80.,-.2),(0.,-1.),(-80.,-1.8)])
def test_money_change_current_zero_and_negative_values(tmp_path,current,expected):
    metric=build(tmp_path,amounts=(50.,50.,current/2,current/2))["kpi_revenue"]
    c=metric.comparison
    assert metric.value==current and c.previous_value==100 and c.delta_abs==current-100
    assert c.delta_pct==pytest.approx(expected) and c.current_range.from_date==date(2025,2,1)
    assert c.previous_range==DateRange(from_date=date(2025,1,1),to_date=date(2025,1,31))


def test_margin_is_percentage_points_and_registry_polarity_is_reused(tmp_path):
    c=build(tmp_path)["kpi_gross_margin_pct"].comparison
    assert c.previous_value==pytest.approx(.4) and c.delta_pp==pytest.approx(5)
    assert c.delta_abs==pytest.approx(.05) and c.delta_pct is None
    assert c.percentage_reason_key=="comparison.percentage_points" and c.direction=="increase"


@pytest.mark.parametrize("profile,metric,previous,current",[("retail_ecommerce","units_sold",2,2),("services","revenue_per_hour",50,60),("hospitality","adr",50,60),("custom","transactions",2,2)])
def test_profile_metrics_and_averages_share_existing_engine(tmp_path,profile,metric,previous,current):
    c=build(tmp_path,profile_id=profile)[f"kpi_{metric}"].comparison
    assert c.status=="ok" and c.previous_value==previous and c.delta_abs==current-previous


def test_baseline_zero_returns_absolute_change_only(tmp_path):
    c=build(tmp_path,amounts=(0.,0.,60.,60.))["kpi_revenue"].comparison
    assert c.status=="previous_zero" and c.delta_abs==120 and c.delta_pct is None
    assert c.percentage_reason_key=="comparison.previous_zero"


def test_negative_baseline_uses_magnitude_without_reversing_change(tmp_path):
    c=build(tmp_path,amounts=(-50.,-50.,-40.,-40.))["kpi_revenue"].comparison
    assert c.delta_abs==20 and c.delta_pct==.2 and c.direction=="increase"


def test_same_segment_and_date_bounds_include_whole_last_day(tmp_path):
    c=build(tmp_path,categories=("A","B","A","B"),filters=[FilterClause(field="date",op="between",values=["2025-02-01","2025-02-28"]),FilterClause(field="category",op="in",values=["B"]),FilterClause(field="channel",op="in",values=["Online"])])["kpi_revenue"].comparison
    assert c.previous_value==50 and c.delta_abs==10


def test_missing_history_and_missing_segment_observations_are_not_zero(tmp_path):
    data=build(tmp_path,dates=[datetime(2025,2,1),datetime(2025,2,2),datetime(2025,2,3),datetime(2025,2,28)])
    assert data["kpi_revenue"].comparison.reason_key=="comparison.insufficient_data"
    filters=[FilterClause(field="date",op="between",values=["2025-02-01","2025-02-28"]),FilterClause(field="category",op="in",values=["B"])]
    c=build(tmp_path,categories=("A","A","B","B"),filters=filters)["kpi_transactions"].comparison
    assert c.reason_key=="comparison.previous_no_observations" and c.previous_value is None
    c=build(tmp_path,categories=("B","B","A","A"),filters=filters)["kpi_transactions"].comparison
    assert c.reason_key=="comparison.current_no_observations" and c.delta_pct is None


@pytest.mark.parametrize("currencies,reason",[(('USD','USD','ARS','ARS'),'comparison.currency_mismatch'),(('USD','ARS','ARS','ARS'),'comparison.currency_mismatch'),(('ARS','ARS','USD','ARS'),'comparison.current_unavailable')])
def test_currency_protections_across_both_windows(tmp_path,currencies,reason):
    data=build(tmp_path,currencies=currencies)
    if reason=="comparison.current_unavailable":
        assert "kpi_revenue" not in data
    else:
        assert data["kpi_revenue"].comparison.reason_key==reason and data["kpi_revenue"].comparison.delta_pct is None


def test_no_date_disabled_and_intraday_filters(tmp_path):
    assert build(tmp_path,dated=False)["kpi_revenue"].comparison.reason_key=="comparison.no_date"
    assert build(tmp_path,mode="none")["kpi_revenue"].comparison is None
    c=build(tmp_path,filters=[FilterClause(field="date",op="between",values=["2025-02-01T12:00:00","2025-02-28T18:00:00"])])["kpi_revenue"].comparison
    assert c.reason_key=="comparison.unsupported_time_filter"


@pytest.mark.parametrize("start,end,prior_start,prior_end",[("2025-09-01","2025-09-30","2025-08-01","2025-08-31"),("2025-07-01","2025-09-30","2025-04-01","2025-06-30"),("2024-01-01","2024-12-31","2023-01-01","2023-12-31"),("2025-09-03","2025-09-30","2025-08-06","2025-09-02")])
def test_calendar_windows_and_custom_equivalent_duration(start,end,prior_start,prior_end):
    r=ComparisonResolver().previous_range("previous_period",DateRange.model_validate({"from":start,"to":end}))
    assert r.model_dump(mode="json",by_alias=True)=={"from":prior_start,"to":prior_end}


def test_partial_periods_unequal_explicit_windows_and_nonfinite_values():
    resolver=ComparisonResolver();current=DateRange(from_date=date(2025,2,1),to_date=date(2025,2,15));coverage=DateCoverage(minimum=date(2025,1,1),maximum=date(2025,2,15))
    c=resolver.resolve("previous_period",current,coverage,120,100,today=date(2025,2,15))
    assert c.partial_period and c.previous_range.to_date==date(2025,1,31)
    assert c.previous_range.from_date==date(2025,1,17)
    assert resolver.resolve("previous_month",current,coverage,120,100).reason_key=="comparison.unequal_periods"
    for value in (math.inf,math.nan):assert resolver.resolve("previous_period",current,coverage,value,100).reason_key=="comparison.invalid_value"


def test_incomplete_historical_current_period_is_explicit(tmp_path):
    filters=[FilterClause(field="date",op="between",values=["2025-02-01","2025-03-10"]) ]
    metric=build(tmp_path,filters=filters)["kpi_revenue"]
    assert metric.comparison.partial_period
    assert any(w.code=="PARTIAL_CURRENT_PERIOD" for w in metric.comparison.warnings)
    filters=[FilterClause(field="date",op="between",values=["2025-02-01","2025-12-31"]) ]
    assert build(tmp_path,filters=filters,dates=[datetime(2024,1,1),datetime(2024,12,31),datetime(2025,2,1),datetime(2025,2,28)])["kpi_revenue"].comparison.reason_key=="comparison.current_insufficient_data"


def test_zero_margin_baseline_and_date_filter_intersection(tmp_path):
    c=build(tmp_path,amounts=(30.,30.,60.,60.))["kpi_gross_margin_pct"].comparison
    assert c.status=="previous_zero" and c.delta_pp==pytest.approx(45) and c.delta_pct is None
    filters=[FilterClause(field="date",op="gte",values=["2025-02-01"]),FilterClause(field="date",op="lte",values=["2025-02-28"])]
    assert build(tmp_path,filters=filters)["kpi_revenue"].comparison.delta_pct==.2
    filters=[FilterClause(field="date",op="between",values=["2025-99-99","2025-02-28"])]
    assert build(tmp_path,filters=filters)["kpi_revenue"].comparison.reason_key=="comparison.unsupported_time_filter"


def test_utc_dates_and_export_row_projection_share_day_bounds(tmp_path):
    dates=[datetime(2025,1,1,tzinfo=timezone.utc),datetime(2025,1,31,23,59,tzinfo=timezone.utc),datetime(2025,2,1,tzinfo=timezone.utc),datetime(2025,2,28,23,59,tzinfo=timezone.utc)]
    assert build(tmp_path,dates=dates)["kpi_revenue"].comparison.delta_pct==.2
    path=tmp_path/"canonical.parquet";engine=PandasDataEngine()
    from analytics_core.engine.query import QuerySpec, MeasureSpec
    filters=[FilterClause(field="date",op="between",values=["2025-02-01","2025-02-28"])]
    count=engine.run_query(path,QuerySpec(measures=[MeasureSpec(alias="rows",aggregation="count")],filters=filters)).rows[0]["rows"]
    exported=list(engine.iter_rows(path,QuerySpec(measures=[],filters=filters),["amount"]))
    assert count==len(exported)==2 and sum(row["amount"] for row in exported)==120
    filters=[FilterClause(field="date",op="between",values=["2025-02-01T00:00:00+00:00","2025-03-01T00:00:00+00:00"])]
    assert build(tmp_path,dates=dates,filters=filters)["kpi_revenue"].comparison.reason_key=="comparison.unsupported_time_filter"


def test_day_bounds_follow_canonical_timezone_across_dst(tmp_path):
    from zoneinfo import ZoneInfo
    from analytics_core.engine.query import QuerySpec, MeasureSpec
    tz=ZoneInfo("Europe/Berlin");path=tmp_path/"dst.parquet"
    pq.write_table(pa.table({"date":[datetime(2024,3,31,23,30,tzinfo=tz),datetime(2024,4,1,0,30,tzinfo=tz)],"amount":[100.,200.]}),path)
    query=QuerySpec(measures=[MeasureSpec(alias="total",aggregation="sum",field="amount")],filters=[FilterClause(field="date",op="between",values=["2024-03-31","2024-03-31"])])
    assert PandasDataEngine().run_query(path,query).rows[0]["total"]==100
