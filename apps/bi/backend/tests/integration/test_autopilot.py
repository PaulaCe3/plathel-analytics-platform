from io import BytesIO

import openpyxl
import pyarrow.parquet as pq
from fastapi.testclient import TestClient

from analytics_core.settings import Settings
from platform_api import create_app


def upload(client, name, content, mime="text/csv"):
    response = client.post("/api/v1/datasets", files={"file": (name, content, mime)})
    assert response.status_code == 201, response.text
    return response.json()["dataset_id"]


def autopilot(client, dataset_id):
    response = client.post(f"/api/v1/datasets/{dataset_id}/autopilot")
    assert response.status_code == 200, response.text
    return response.json()


def test_csv_autopilot_detects_profile_maps_prepares_and_preserves_rows(tmp_path):
    csv = "fecha_compra,articulo,valor_total,canal\n2025-01-01,  Mate  ,100,Online\n2025-01-01,  Mate  ,100,Online\n"
    with TestClient(create_app(Settings(dataset_storage_path=tmp_path)), raise_server_exceptions=False) as client:
        dataset_id = upload(client, "ventas.csv", csv)
        result = autopilot(client, dataset_id)
        assert result["status"] == "ready" and result["stage"] == "ready"
        assert result["profile_id"] == "retail_ecommerce" and result["destination"] == "results"
        dataset = client.get(f"/api/v1/datasets/{dataset_id}").json()
        assert dataset["canonical_row_count"] == 2 and dataset["cleaning_confirmed"]
        frame = pq.read_table(tmp_path / dataset_id / "canonical.parquet").to_pydict()
        assert frame["concept"] == ["Mate", "Mate"]
        assert client.post(f"/api/v1/datasets/{dataset_id}/dashboard", json={}).status_code == 200


def test_ambiguous_industry_uses_custom_and_nonessential_column_does_not_block(tmp_path):
    csv = "fecha,importe,nota_interna\n2025-01-01,10,uno\n2025-02-01,20,dos\n"
    with TestClient(create_app(Settings(dataset_storage_path=tmp_path)), raise_server_exceptions=False) as client:
        dataset_id = upload(client, "actividad.csv", csv)
        result = autopilot(client, dataset_id)
        assert result["status"] == "ready" and result["profile_id"] == "custom"
        session = client.get(f"/api/v1/datasets/{dataset_id}").json()
        assert session["row_count"] == session["canonical_row_count"] == 2


def test_autopilot_never_applies_destructive_duplicate_removal(tmp_path):
    csv = "fecha,importe\n2025-01-01,10\n2025-01-01,10\n"
    with TestClient(create_app(Settings(dataset_storage_path=tmp_path)), raise_server_exceptions=False) as client:
        dataset_id = upload(client, "duplicados.csv", csv)
        assert autopilot(client, dataset_id)["status"] == "ready"
        session = client.get(f"/api/v1/datasets/{dataset_id}").json()
        assert session["canonical_row_count"] == 2
        transformations = client.get(f"/api/v1/datasets/{dataset_id}/transformations").json()["transformations"]
        assert not any(item["action_id"] == "drop_exact_duplicates" for item in transformations)


def test_xlsx_autopilot_reaches_ready(tmp_path):
    workbook = openpyxl.Workbook(); sheet = workbook.active
    sheet.append(["fecha", "importe", "grupo"]); sheet.append(["2025-01-01", 10, "A"]); sheet.append(["2025-02-01", 20, "B"])
    content = BytesIO(); workbook.save(content)
    with TestClient(create_app(Settings(dataset_storage_path=tmp_path)), raise_server_exceptions=False) as client:
        dataset_id = upload(client, "datos.xlsx", content.getvalue(), "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        assert autopilot(client, dataset_id)["status"] == "ready"


def test_real_blockers_fall_back_without_fabricating_analysis(tmp_path):
    cases = {
        "sin_fecha.csv": "importe,cliente\n10,A\n20,B\n",
        "sin_metrica.csv": "fecha,cliente\n2025-01-01,A\n2025-02-01,B\n",
        "conflicto.csv": "fecha,importe,total\n2025-01-01,10,10\n",
    }
    with TestClient(create_app(Settings(dataset_storage_path=tmp_path)), raise_server_exceptions=False) as client:
        for name, csv in cases.items():
            dataset_id = upload(client, name, csv)
            result = autopilot(client, dataset_id)
            assert result["status"] == "intervention_required" and result["destination"] == "mapping"
            assert client.get(f"/api/v1/datasets/{dataset_id}").json()["stage"] == "parsed"


def test_forecast_absence_does_not_block_and_sufficient_history_remains_available(tmp_path):
    short = "fecha,importe\n2025-01-01,10\n2025-02-01,20\n"
    rows = [f"{2022 + index // 12}-{index % 12 + 1:02d}-01,{index % 12 + 1}" for index in range(36)]
    long = "fecha,importe\n" + "\n".join(rows) + "\n"
    with TestClient(create_app(Settings(dataset_storage_path=tmp_path)), raise_server_exceptions=False) as client:
        short_id = upload(client, "corto.csv", short); long_id = upload(client, "largo.csv", long)
        assert autopilot(client, short_id)["status"] == "ready"
        assert client.get(f"/api/v1/forecast/datasets/{short_id}/options").json()["status"] == "unavailable"
        assert autopilot(client, long_id)["status"] == "ready"
        assert client.get(f"/api/v1/forecast/datasets/{long_id}/options").json()["status"] == "ok"
