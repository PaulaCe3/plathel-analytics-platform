from io import BytesIO
from pathlib import Path

from fastapi.testclient import TestClient
from openpyxl import Workbook

from analytics_core.settings import Settings
from bi.api.main import create_app


def make_client(tmp_path: Path) -> TestClient:
    return TestClient(create_app(Settings(dataset_storage_path=tmp_path)), raise_server_exceptions=False)


def xlsx_bytes() -> bytes:
    workbook = Workbook()
    first = workbook.active
    first.title = "Primera"
    first.append(["informe"])
    first.append(["nombre", "importe"])
    first.append(["Ana", 10])
    second = workbook.create_sheet("Segunda")
    second.append(["producto", "cantidad"])
    second.append(["Mate", 2])
    buffer = BytesIO()
    workbook.save(buffer)
    return buffer.getvalue()


def test_csv_upload_preview_get_and_delete(tmp_path: Path) -> None:
    with make_client(tmp_path) as client:
        response = client.post("/api/v1/datasets", files={"file": ("ventas.csv", "nombre;ciudad;nombre\nJosé;Córdoba;Pepe\n", "text/csv")})
        assert response.status_code == 201, response.text
        dataset = response.json()
        assert dataset["stage"] == "parsed"
        assert [column["key"] for column in dataset["columns"]] == ["c01", "c02", "c03"]
        assert dataset["columns"][2]["original_name"] == "nombre"
        dataset_id = dataset["dataset_id"]
        assert client.get(f"/api/v1/datasets/{dataset_id}").status_code == 200
        preview = client.get(f"/api/v1/datasets/{dataset_id}/preview?rows=10")
        assert preview.json()["rows"][0]["c02"] == "Córdoba"
        assert client.delete(f"/api/v1/datasets/{dataset_id}").status_code == 204
        assert client.get(f"/api/v1/datasets/{dataset_id}").status_code == 404


def test_xlsx_upload_sheet_selection_and_invalid_inputs(tmp_path: Path) -> None:
    with make_client(tmp_path) as client:
        response = client.post("/api/v1/datasets", files={"file": ("libro.xlsx", xlsx_bytes(), "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")})
        assert response.status_code == 201, response.text
        dataset = response.json()
        assert dataset["available_sheets"] == ["Primera", "Segunda"]
        changed = client.patch(f"/api/v1/datasets/{dataset['dataset_id']}", json={"sheet": "Segunda"})
        assert changed.status_code == 200, changed.text
        preview = client.get(f"/api/v1/datasets/{dataset['dataset_id']}/preview").json()
        assert preview["selected_sheet"] == "Segunda"
        assert preview["rows"][0]["c01"] == "Mate"
        assert client.get("/api/v1/datasets/not-found").status_code == 404
        invalid = client.post("/api/v1/datasets", files={"file": ("bad.xlsx", b"invalid", "application/octet-stream")})
        assert invalid.status_code == 422
