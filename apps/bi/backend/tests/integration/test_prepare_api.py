from pathlib import Path

import pyarrow.parquet as pq
from fastapi.testclient import TestClient

from analytics_core.settings import Settings
from bi.api.main import create_app


def test_complete_prepare_clean_reset_flow(tmp_path: Path) -> None:
    csv = "fecha_compra,articulo,importe,segmento\n2026-01-01,  Mate  ,100,Mayorista\n2026-01-01,  Mate  ,100,Mayorista\nfecha mala,Café,texto,Minorista\n"
    with TestClient(create_app(Settings(dataset_storage_path=tmp_path)), raise_server_exceptions=False) as client:
        uploaded = client.post("/api/v1/datasets", files={"file": ("dirty.csv", csv, "text/csv")}).json()
        dataset_id = uploaded["dataset_id"]
        mapping = {"profile_id": "retail_ecommerce", "mappings": [
            {"column_key": "c01", "target_field": "date", "disposition": "canonical"},
            {"column_key": "c02", "target_field": "concept", "disposition": "canonical"},
            {"column_key": "c03", "target_field": "amount", "disposition": "canonical"},
            {"column_key": "c04", "target_field": None, "disposition": "custom_dimension"},
        ]}
        assert client.put(f"/api/v1/datasets/{dataset_id}/mapping", json=mapping).json()["stage"] == "mapped"
        raw_path = tmp_path / dataset_id / "raw.parquet"
        raw_before = raw_path.read_bytes()
        validated = client.post(f"/api/v1/datasets/{dataset_id}/validate")
        assert validated.status_code == 200, validated.text
        assert validated.json()["stage"] == "validated"
        assert (tmp_path / dataset_id / "canonical.parquet").exists()
        cleaning = client.put(f"/api/v1/datasets/{dataset_id}/cleaning", json={"actions": [
            {"id": "trim_whitespace", "description": "trim"},
            {"id": "drop_exact_duplicates", "destructive": True, "description": "duplicates"},
        ]})
        assert cleaning.status_code == 200, cleaning.text
        assert cleaning.json()["stage"] == "ready" and cleaning.json()["canonical_row_count"] == 2
        log = client.get(f"/api/v1/datasets/{dataset_id}/transformations").json()["transformations"]
        assert any(item["action_id"] == "drop_exact_duplicates" for item in log)
        reset = client.put(f"/api/v1/datasets/{dataset_id}/cleaning", json={"actions": []}).json()
        assert reset["canonical_row_count"] == 3
        dataset = client.get(f"/api/v1/datasets/{dataset_id}").json()
        assert dataset["stage"] == "ready" and dataset["has_canonical"] and dataset["cleaning_confirmed"]
        assert raw_path.read_bytes() == raw_before
        assert client.delete(f"/api/v1/datasets/{dataset_id}").status_code == 204


def test_validate_requires_mapped_stage(tmp_path: Path) -> None:
    with TestClient(create_app(Settings(dataset_storage_path=tmp_path)), raise_server_exceptions=False) as client:
        dataset = client.post("/api/v1/datasets", files={"file": ("data.csv", "fecha,importe\n2026-01-01,10\n", "text/csv")}).json()
        response = client.post(f"/api/v1/datasets/{dataset['dataset_id']}/validate")
        assert response.status_code == 409
        assert response.json()["error"]["code"] == "STAGE_NOT_READY"
