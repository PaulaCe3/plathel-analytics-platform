"""Typed temporal-column discovery; dataframe objects stay inside the engine."""
from pathlib import Path
import pyarrow as pa
import pyarrow.parquet as pq


def temporal_columns(path: Path) -> tuple[list[str], list[str]]:
    public = [field for field in pq.read_schema(path) if not field.name.startswith("_")]
    dates = [field.name for field in public if pa.types.is_timestamp(field.type) or pa.types.is_date(field.type)]
    measures = [field.name for field in public if pa.types.is_integer(field.type) or pa.types.is_floating(field.type) or pa.types.is_decimal(field.type)]
    return dates, measures
