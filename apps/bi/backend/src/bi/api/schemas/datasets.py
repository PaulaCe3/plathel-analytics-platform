"""HTTP schemas for Phase 1 datasets."""

from datetime import datetime

from typing import Literal
from pydantic import BaseModel, Field

from analytics_core.ingestion.models import ColumnMetadata, SourceSettings
from analytics_core.sessions.models import FileMetadata
from analytics_core.quality.models import QualitySummary


class DatasetResponse(BaseModel):
    dataset_id: str
    stage: str
    industry_id: str | None
    demo_id: str | None = None
    source_settings: SourceSettings
    created_at: datetime
    updated_at: datetime
    expires_at: datetime
    selected_sheet: str | None
    available_sheets: list[str]
    file: FileMetadata | None
    parsing_status: str
    row_count: int
    column_count: int
    columns: list[ColumnMetadata]
    warnings: list[str]
    has_canonical: bool
    canonical_row_count: int | None
    validation_status: str | None
    quality_summary: QualitySummary | None
    cleaning_confirmed: bool


class DatasetPatch(BaseModel):
    sheet: str | None = None
    header_row: int | None = Field(default=None, ge=0)
    industry_id: str | None = None


class PreviewResponse(BaseModel):
    dataset_id: str
    row_count: int
    column_count: int
    selected_sheet: str | None
    columns: list[ColumnMetadata]
    rows: list[dict[str, str | None]]
    warnings: list[str]


class AutopilotResponse(BaseModel):
    dataset_id: str
    status: Literal["ready", "intervention_required"]
    stage: str
    profile_id: str
    explanation: str
    destination: str
