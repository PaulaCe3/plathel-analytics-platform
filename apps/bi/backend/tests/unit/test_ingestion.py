from io import BytesIO
from pathlib import Path

import pytest
from openpyxl import Workbook

from analytics_core.engine.pandas_impl import PandasDataEngine
from analytics_core.errors import AppError
from analytics_core.ingestion.headers import normalize_headers
from analytics_core.ingestion.models import SourceSettings
from analytics_core.ingestion.sniffing import detect_delimiter, detect_encoding
from analytics_core.security.uploads import validate_extension, validate_xlsx
from analytics_core.sources import UploadSource


def test_detects_csv_dialect_and_spanish_encoding() -> None:
    assert detect_delimiter("nombre;ciudad\nJosé;Córdoba") == ";"
    assert detect_encoding("año".encode("cp1252")) == "cp1252"


def test_normalizes_empty_and_duplicate_headers() -> None:
    originals, headers = normalize_headers([" nombre\n", "", "nombre", "nombre"])
    assert originals == [" nombre\n", "", "nombre", "nombre"]
    assert headers == ["nombre", "columna_2", "nombre_2", "nombre_3"]


def test_rejects_empty_oversized_unsupported_and_traversal(tmp_path: Path) -> None:
    source = UploadSource()
    with pytest.raises(AppError, match="vacío"):
        source.save(BytesIO(b""), "data.csv", tmp_path / "empty", allowed_extensions=(".csv", ".xlsx"), max_bytes=5)
    with pytest.raises(AppError, match="tamaño"):
        source.save(BytesIO(b"123456"), "data.csv", tmp_path / "large", allowed_extensions=(".csv", ".xlsx"), max_bytes=5)
    with pytest.raises(AppError):
        validate_extension("data.xls", (".csv", ".xlsx"))
    with pytest.raises(AppError):
        validate_extension("../data.csv", (".csv", ".xlsx"))


def test_reads_valid_xlsx_and_rejects_corrupt(tmp_path: Path) -> None:
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Resumen"
    sheet.append(["reporte"])
    sheet.append(["nombre", "valor"])
    sheet.append(["uno", 1])
    second = workbook.create_sheet("Detalle")
    second.append(["código", "descripción"])
    second.append(["A", "Árbol"])
    xlsx = tmp_path / "valid.xlsx"
    workbook.save(xlsx)
    validate_xlsx(xlsx, 5_000_000)
    result = PandasDataEngine().parse_to_parquet(xlsx, ".xlsx", tmp_path / "raw.parquet", SourceSettings(), max_rows=100, max_columns=10)
    assert result.available_sheets == ["Resumen", "Detalle"]
    assert result.selected_sheet == "Resumen"
    assert result.source_settings.header_row == 1
    corrupt = tmp_path / "bad.xlsx"
    corrupt.write_bytes(b"not a zip")
    with pytest.raises(AppError):
        validate_xlsx(corrupt, 1000)
