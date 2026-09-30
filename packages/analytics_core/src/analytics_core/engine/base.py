"""Engine interface that prevents dataframe types from escaping."""

from pathlib import Path
from collections.abc import Iterator
from typing import Protocol

from analytics_core.ingestion.models import ParseResult, SourceSettings
from analytics_core.canonical.derived import DerivedFieldRule
from analytics_core.canonical.fields import FieldSpec
from analytics_core.cleaning.models import CanonicalBuildResult, CleaningActionSpec, CleaningPlan
from analytics_core.mapping.models import ColumnMapping
from analytics_core.quality.models import DataQualityReport
from analytics_core.validation.models import ParseReport, ProfileCheck
from analytics_core.engine.query import DateCoverage, QueryResult, QuerySpec, Scalar


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

    def build_canonical(self, raw_path: Path, destination: Path, mappings: list[ColumnMapping], fields: list[FieldSpec], column_names: dict[str, str], settings: SourceSettings, derived_rules: list[DerivedFieldRule], actions: list[CleaningActionSpec]) -> CanonicalBuildResult: ...

    def inspect_quality(self, canonical_path: Path, reports: list[ParseReport], profile_checks: list[ProfileCheck]) -> DataQualityReport: ...

    def create_cleaning_plan(self, canonical_path: Path, reports: list[ParseReport], quality: DataQualityReport) -> CleaningPlan: ...

    def run_query(self, canonical_path: Path, query: QuerySpec) -> QueryResult: ...

    def iter_rows(self, canonical_path: Path, query: QuerySpec, columns: list[str]) -> Iterator[dict[str, Scalar]]: ...

    def date_coverage(self, canonical_path: Path, field: str) -> DateCoverage: ...

    def temporal_columns(self, canonical_path: Path) -> tuple[list[str], list[str]]: ...
