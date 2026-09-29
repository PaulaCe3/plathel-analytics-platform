from pathlib import Path

from fastapi.testclient import TestClient

from analytics_core.settings import Settings
from bi.api.main import create_app


def test_mapping_flow_is_persistent_idempotent_and_invalidated(tmp_path: Path) -> None:
    with TestClient(create_app(Settings(dataset_storage_path=tmp_path)), raise_server_exceptions=False) as client:
        uploaded = client.post("/api/v1/datasets", files={"file": ("retail.csv", "fecha_compra,articulo,valor_total,segmento\n2026-01-01,Mate,150,Mayorista\n", "text/csv")}).json()
        dataset_id = uploaded["dataset_id"]
        assert uploaded["stage"] == "parsed"
        changed = client.patch(f"/api/v1/datasets/{dataset_id}", json={"industry_id": "retail_ecommerce"})
        assert changed.status_code == 200
        view = client.get(f"/api/v1/datasets/{dataset_id}/mapping").json()
        suggestions = {item["column_key"]: item["candidates"][0]["field_id"] for item in view["suggestions"] if item["candidates"]}
        assert suggestions == {"c01": "date", "c02": "concept", "c03": "amount"}
        request = {"profile_id": "retail_ecommerce", "mappings": [
            {"column_key": "c01", "target_field": "date", "disposition": "canonical"},
            {"column_key": "c02", "target_field": "concept", "disposition": "canonical"},
            {"column_key": "c03", "target_field": "amount", "disposition": "canonical"},
            {"column_key": "c04", "target_field": None, "disposition": "custom_dimension"},
        ]}
        first = client.put(f"/api/v1/datasets/{dataset_id}/mapping", json=request)
        second = client.put(f"/api/v1/datasets/{dataset_id}/mapping", json=request)
        assert first.status_code == second.status_code == 200
        assert second.json()["stage"] == "mapped"
        assert client.get(f"/api/v1/datasets/{dataset_id}").json()["stage"] == "mapped"
        reset = client.patch(f"/api/v1/datasets/{dataset_id}", json={"industry_id": "services"}).json()
        assert reset["stage"] == "parsed"
        assert client.get(f"/api/v1/datasets/{dataset_id}/mapping").json()["mappings"] == []


def test_profiles_and_blocking_conflict(tmp_path: Path) -> None:
    with TestClient(create_app(Settings(dataset_storage_path=tmp_path)), raise_server_exceptions=False) as client:
        assert {item["id"] for item in client.get("/api/v1/profiles").json()} >= {"custom", "services", "hospitality"}
        hospitality = client.get("/api/v1/profiles/hospitality").json()
        assert {field["id"] for field in hospitality["fields"]} >= {"check_in", "booking_date", "room_type"}
        uploaded = client.post("/api/v1/datasets", files={"file": ("bad.csv", "fecha,importe\ntexto,tambien texto\n", "text/csv")}).json()
        response = client.put(f"/api/v1/datasets/{uploaded['dataset_id']}/mapping", json={"profile_id": "retail_ecommerce", "mappings": [
            {"column_key": "c01", "target_field": "date", "disposition": "canonical"},
            {"column_key": "c02", "target_field": "amount", "disposition": "canonical"},
        ]})
        assert response.status_code == 422
        assert response.json()["error"]["code"] == "MAPPING_INVALID"
