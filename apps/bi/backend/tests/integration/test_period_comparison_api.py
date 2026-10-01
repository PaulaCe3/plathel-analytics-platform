import pytest
from fastapi.testclient import TestClient
from analytics_core.settings import Settings
from bi.api.main import create_app


@pytest.mark.parametrize("dated",[True,False])
def test_existing_dashboard_api_returns_automatic_comparisons_without_mutating_raw(tmp_path,dated):
    rows=["2025-01-01,50,30,A,ARS","2025-01-31,50,30,A,ARS","2025-02-01,60,33,A,ARS","2025-02-28,60,33,A,ARS"]
    csv="fecha,importe,costo,segmento,moneda\n"+"\n".join(rows)
    if not dated:csv="\n".join(line.split(",",1)[1] for line in csv.splitlines())
    with TestClient(create_app(Settings(dataset_storage_path=tmp_path))) as client:
        uploaded=client.post("/api/v1/datasets",files={"file":("periods.csv",csv,"text/csv")});assert uploaded.status_code==201
        id=uploaded.json()["dataset_id"];prefix=f"/api/v1/datasets/{id}";raw=tmp_path/id/"raw.parquet";before=raw.read_bytes()
        fields=(["date"] if dated else [])+["amount","cost","category","currency"]
        mappings=[{"column_key":f"c{i+1:02}","target_field":None if field=="cost" and not dated else field,"disposition":"ignored" if field=="cost" and not dated else "canonical","options":{"basis":"total"} if field=="cost" and dated else {}} for i,field in enumerate(fields)]
        assert client.put(prefix+"/mapping",json={"profile_id":"retail_ecommerce" if dated else "custom","mappings":mappings}).status_code==200
        assert client.post(prefix+"/validate").status_code==200
        assert client.put(prefix+"/cleaning",json={"actions":[]}).status_code==200
        filters=[{"field":"category","op":"in","values":["A"]}]
        if dated:filters.append({"field":"date","op":"between","values":["2025-02-01","2025-02-28"]})
        response=client.post(prefix+"/dashboard",json={"filters":filters});assert response.status_code==200,response.text
        data=response.json()["data"];c=data["kpi_revenue"]["comparison"]
        if dated:
            assert data["kpi_revenue"]["value"]==120 and c["previous_value"]==100
            assert c["delta_pct"]==pytest.approx(.2) and c["current_range"]=={"from":"2025-02-01","to":"2025-02-28"}
            assert c["previous_range"]=={"from":"2025-01-01","to":"2025-01-31"}
            margin=data["kpi_gross_margin_pct"]["comparison"];assert margin["delta_pp"]==pytest.approx(5) and margin["delta_pct"] is None
        else:
            assert data["kpi_revenue"]["value"]==220 and c["reason_key"]=="comparison.no_date"
            assert client.post(prefix+"/dashboard",json={"time_field":"date"}).status_code==422
        assert client.post(prefix+"/dashboard",json={"filters":filters,"comparison":{"mode":"none"}}).json()["data"]["kpi_revenue"]["comparison"] is None
        assert raw.read_bytes()==before
