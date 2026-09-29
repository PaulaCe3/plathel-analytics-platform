"""Persisted metadata for a temporary raw dataset."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from analytics_core.ingestion.models import ColumnMetadata, SourceSettings
from analytics_core.mapping.models import ColumnMapping


class FileMetadata(BaseModel):
    original_name: str
    extension: str
    size_bytes: int


class DatasetSession(BaseModel):
    dataset_id: str
    stage: Literal["created", "parsed", "mapped"] = "created"
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
