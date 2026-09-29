"""Persisted metadata for a temporary raw dataset."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from analytics_core.ingestion.models import ColumnMetadata, SourceSettings
from analytics_core.mapping.models import ColumnMapping
from analytics_core.cleaning.models import CleaningActionSpec, CleaningPlan, TransformationLog
from analytics_core.quality.models import QualitySummary
from analytics_core.validation.models import ParseReport, ValidationReport


class FileMetadata(BaseModel):
    original_name: str
    extension: str
    size_bytes: int


class DatasetSession(BaseModel):
    dataset_id: str
    stage: Literal["created", "parsed", "mapped", "validated", "ready"] = "created"
    industry_id: str | None = None
    source_settings: SourceSettings = Field(default_factory=SourceSettings)
    created_at: datetime
    updated_at: datetime
    expires_at: datetime
    selected_sheet: str | None = None
    available_sheets: list[str] = Field(default_factory=list)
    file: FileMetadata | None = None
    parsing_status: str = "pending"
    row_count: int = 0
    column_count: int = 0
    columns: list[ColumnMetadata] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    mappings: list[ColumnMapping] = Field(default_factory=list)
    has_canonical: bool = False
    canonical_row_count: int | None = None
    canonical_columns: list[str] = Field(default_factory=list)
    validation_status: str | None = None
    validation_report: ValidationReport | None = None
    parse_reports: list[ParseReport] = Field(default_factory=list)
    quality_summary: QualitySummary | None = None
    cleaning_plan: CleaningPlan | None = None
    cleaning_actions: list[CleaningActionSpec] = Field(default_factory=list)
    cleaning_confirmed: bool = False
    transformation_log: TransformationLog = Field(default_factory=TransformationLog)
