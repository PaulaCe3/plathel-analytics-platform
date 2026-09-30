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
    assert estimate(changed,"quantity","Cantidad",3,today=date(2024,1,1)).evaluation_value==1


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
