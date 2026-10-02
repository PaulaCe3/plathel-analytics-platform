"""Product composition tests: shared prepared data, no fabricated forecasts."""
from datetime import date, datetime
import hashlib
import pyarrow as pa
import pyarrow.parquet as pq
import pytest
from fastapi.testclient import TestClient
from analytics_core.settings import Settings
from analytics_core.sessions.store import DatasetSessionStore
from forecast.model import estimate, period_name
from forecast.models import ForecastPoint
from forecast.engine import PREDICTION_COVERAGE, _rolling_errors, empirical_range, select_forecast
from platform_api import create_app


def points(length=24):
    return [ForecastPoint(period=period_name(2020*12+i), value=float(i % 12 + 1)) for i in range(length)]


def test_seasonal_forecast_and_held_out_evaluation():
    result=estimate(points(),"quantity","Cantidad",3,today=date(2024,1,1))
    assert result.status=="ok"
    assert [point.value for point in result.prediction]==[1,2,3]
    assert result.prediction[0].period=="2022-01"
    assert result.evaluation_value==0
    changed=points();changed[-1]=changed[-1].model_copy(update={"value":18})
    assert estimate(changed,"quantity","Cantidad",3,today=date(2024,1,1)).evaluation_value==pytest.approx(1/3)


def test_model_selection_for_constant_trend_and_seasonality():
    constant=select_forecast([8.0]*30,3)
    trend=select_forecast([float(index*4-20) for index in range(30)],3)
    seasonal=select_forecast([float((index%12+1)**2) for index in range(36)],3)
    assert constant and constant.candidate.id=="naive"
    assert trend and trend.candidate.id=="linear_trend"
    assert seasonal and seasonal.candidate.id=="seasonal_naive"
    assert trend.mae==pytest.approx(0)
    assert [round(value) for value in trend.values]==[100,104,108]


def test_rolling_origin_uses_only_prior_values_and_requested_horizon():
    class RecordingCandidate:
        id="recording";name="Recording";complexity=0;minimum_history=1
        def __init__(self):self.training=[]
        def predict(self,history,horizon):self.training.append(list(history));return [history[-1]]*horizon
    candidate=RecordingCandidate()
    errors=_rolling_errors(candidate,[float(value) for value in range(20)],4)
    assert all(len(step)==6 for step in errors)
    assert all(training==[float(value) for value in range(len(training))] for training in candidate.training)
    assert max(map(len,candidate.training))==16


def test_empirical_ranges_are_asymmetric_finite_and_require_evidence():
    assert empirical_range(10,[1,2]) is None
    bounds=empirical_range(10,[-4,-2,1,3,8,10])
    assert bounds is not None and bounds[0] <= 10 <= bounds[1]
    assert bounds[1]-10 != 10-bounds[0]
    assert PREDICTION_COVERAGE==0.80


@pytest.mark.parametrize("horizon",[1,4,6])
def test_forecast_horizon_mae_contract_and_ranges(horizon):
    result=estimate(points(36),"quantity","Cantidad",horizon,today=date(2024,1,1))
    assert result.status=="ok" and len(result.prediction)==horizon
    assert result.evaluation_value==pytest.approx(0)
    assert result.evaluation_periods >= horizon
    assert {item.model_id for item in result.candidate_evaluations}=={"naive","seasonal_naive","linear_trend"}
    assert all(point.lower is not None and point.lower <= point.value <= point.upper for point in result.prediction)


@pytest.mark.parametrize("kind",["short","gap","invalid","incomplete","nonfinite"])
def test_unavailable_history_never_returns_prediction(kind):
    history=points()
    today=date(2024,1,1)
    excluded=0
    if kind=="short":history=history[:23]
    if kind=="gap":history=points(25);history.pop(12)
    if kind=="invalid":excluded=1
    if kind=="incomplete":today=date(2021,12,1)
    if kind=="nonfinite":history[-1]=history[-1].model_copy(update={"value":float("inf")})
    result=estimate(history,"quantity","Cantidad",3,excluded,today)
    assert result.status=="unavailable" and not result.prediction


def test_shared_session_forecast_contract_and_raw_immutability(tmp_path):
    settings=Settings(dataset_storage_path=tmp_path)
    store=DatasetSessionStore(tmp_path,settings.dataset_ttl_minutes)
    session=store.create()
    session.stage="ready";session.has_canonical=True;session.cleaning_confirmed=True
    session.canonical_columns=["date","quantity","amount","currency"]
    history=points(36)
    table=pa.table({"date":pa.array([datetime.fromisoformat(p.period+"-01") for p in history],type=pa.timestamp("ns")),"quantity":[p.value for p in history],"amount":[p.value*10 for p in history],"currency":["ARS"]*36})
    pq.write_table(table,store.path(session.dataset_id,"canonical.parquet"))
    raw=store.path(session.dataset_id,"raw.parquet");raw.write_bytes(b"immutable original")
    before=hashlib.sha256(raw.read_bytes()).digest()
    store.save(session)
    with TestClient(create_app(settings)) as client:
        path=f"/api/v1/forecast/datasets/{session.dataset_id}"
        options=client.get(path+"/options")
        assert options.status_code==200 and options.json()["status"]=="ok"
        assert {choice["field"] for choice in options.json()["choices"]}=={"quantity","amount"}
        result=client.post(path+"/prediction",json={"field":"quantity","horizon":6})
        assert result.status_code==200 and len(result.json()["prediction"])==6
        assert result.json()["evaluation_metric"]=="Error absoluto medio"
        assert result.json()["evaluation_periods"]==36
        assert all(point["lower"] <= point["value"] <= point["upper"] for point in result.json()["prediction"])
        assert {item["model_id"] for item in result.json()["candidate_evaluations"]}=={"naive","seasonal_naive","linear_trend"}
        assert client.post(path+"/prediction",json={"field":"quantity","horizon":7}).status_code==422
        assert client.post(path+"/prediction",json={"field":"not_a_column"}).json()["status"]=="unavailable"
        mixed=table.set_column(3,"currency",pa.array(["ARS"]*35+["USD"]))
        pq.write_table(mixed,store.path(session.dataset_id,"canonical.parquet"))
        assert client.post(path+"/prediction",json={"field":"amount"}).json()["status"]=="unavailable"
        missing=table.set_column(3,"currency",pa.array(["ARS"]*35+[None]))
        pq.write_table(missing,store.path(session.dataset_id,"canonical.parquet"))
        assert client.post(path+"/prediction",json={"field":"amount"}).json()["status"]=="unavailable"
        assert client.get("/api/v1/forecast/datasets/bad/options").status_code==404
    assert hashlib.sha256(raw.read_bytes()).digest()==before


def test_unprepared_session_is_unavailable(tmp_path):
    settings=Settings(dataset_storage_path=tmp_path)
    session=DatasetSessionStore(tmp_path,settings.dataset_ttl_minutes).create()
    with TestClient(create_app(settings)) as client:
        result=client.get(f"/api/v1/forecast/datasets/{session.dataset_id}/options")
        assert result.status_code==200 and result.json()["status"]=="unavailable"


def test_forecast_demo_real_pipeline(tmp_path):
    with TestClient(create_app(Settings(dataset_storage_path=tmp_path))) as client:
        response = client.post("/api/v1/datasets/demo", json={"demo_id": "retail_forecast_demo"})
        assert response.status_code == 201
        dataset = response.json()["dataset_id"]
        assert response.json()["stage"] == "ready"
        assert client.post(f"/api/v1/datasets/{dataset}/dashboard", json={}).status_code == 200
        forecast = client.post(f"/api/v1/forecast/datasets/{dataset}/prediction", json={"field": "quantity", "horizon": 3})
        assert forecast.status_code == 200
        assert forecast.json()["status"] == "ok"
        assert forecast.json()["observations"] == 36
        assert len(forecast.json()["prediction"]) == 3
