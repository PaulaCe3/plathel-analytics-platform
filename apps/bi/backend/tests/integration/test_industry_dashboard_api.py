import pytest
from fastapi.testclient import TestClient
from analytics_core.settings import Settings
from bi.api.main import create_app


@pytest.mark.parametrize("profile,metric,extra,value", [("retail_ecommerce", "gross_profit", "cost", 120), ("services", "revenue_per_hour", "duration_hours", 50), ("hospitality", "adr", "nights", 100), ("custom", "revenue", "quantity", 200)])
def test_phase6_full_api_flow(tmp_path, profile, metric, extra, value):
    date_field = "check_in" if profile == "hospitality" else "date"
    extra_value = {"cost": 80, "duration_hours": 4, "nights": 2, "quantity": 2}[extra]
    # A custom measure comes before a dimension: classification must follow mappings.
    csv = f"fecha,importe,{extra},presupuesto,segmento\n2025-02-01,200,{extra_value},99,A\n"
    with TestClient(create_app(Settings(dataset_storage_path=tmp_path)), raise_server_exceptions=False) as client:
        upload = client.post("/api/v1/datasets", files={"file": ("industry.csv", csv, "text/csv")})
        assert upload.status_code == 201, upload.text
        dataset_id = upload.json()["dataset_id"]
        prefix = f"/api/v1/datasets/{dataset_id}"
        mappings = [{"column_key": "c01", "target_field": date_field, "disposition": "canonical"}, {"column_key": "c02", "target_field": "amount", "disposition": "canonical"}, {"column_key": "c03", "target_field": extra, "disposition": "canonical", "options": {"basis": "total"} if extra == "cost" else {}}, {"column_key": "c04", "disposition": "custom_measure"}, {"column_key": "c05", "disposition": "custom_dimension"}]
        saved = client.put(prefix + "/mapping", json={"profile_id": profile, "mappings": mappings})
        assert saved.status_code == 200, saved.text
        raw = tmp_path / dataset_id / "raw.parquet"
        before = raw.read_bytes()
        assert client.post(prefix + "/validate").status_code == 200
        clean = client.put(prefix + "/cleaning", json={"actions": []})
        assert clean.status_code == 200, clean.text
        response = client.post(prefix + "/dashboard", json={"filters": [{"field": "custom__segmento", "op": "in", "values": ["A"]}]})
        assert response.status_code == 200, response.text
        body = response.json()
        assert body["data"][f"kpi_{metric}"]["value"] == value
        assert "revenue_by_custom__segmento" in body["data"]
        assert "revenue_by_custom__presupuesto" not in body["data"]
        assert raw.read_bytes() == before
        if profile == "retail_ecommerce":
            # Removing explicit metadata must disable profitability, without false zero.
            mappings[2]["options"] = {}
            assert client.put(prefix + "/mapping", json={"profile_id": profile, "mappings": mappings}).status_code == 200
            assert client.post(prefix + "/validate").status_code == 200
            assert client.put(prefix + "/cleaning", json={"actions": []}).status_code == 200
            body = client.post(prefix + "/dashboard", json={}).json()
            assert "kpi_gross_profit" not in body["data"]
            unavailable = next(item for item in body["spec"]["unavailable_metrics"] if item["metric_id"] == "gross_profit")
            assert unavailable["reason_key"] == "metric.requires_cost_basis_total"
