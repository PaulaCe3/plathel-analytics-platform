"""Engine interface that prevents dataframe types from escaping."""

from pathlib import Path
from typing import Protocol

from analytics_core.ingestion.models import ParseResult, SourceSettings


class DataEngine(Protocol):
    def parse_to_parquet(
        self,
        source_path: Path,
        extension: str,
        destination: Path,
        settings: SourceSettings,
        *,
        max_rows: int,
        max_columns: int,
    ) -> ParseResult: ...

    def preview(self, parquet_path: Path, rows: int) -> list[dict[str, str | None]]: ...
