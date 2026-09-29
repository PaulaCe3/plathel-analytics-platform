"""Transport-neutral models for raw ingestion."""

from pydantic import BaseModel, Field


class SourceSettings(BaseModel):
    encoding: str | None = None
    delimiter: str | None = None
    sheet: str | None = None
    header_row: int | None = Field(default=None, ge=0)
    decimal: str | None = None
    thousands: str | None = None
    date_dayfirst: bool | None = None
    date_format: str | None = None


class ColumnMetadata(BaseModel):
    key: str
    original_name: str
    detected_type: str = "string"
    sample: list[str | None] = Field(default_factory=list)
    null_ratio: float = 0.0
    approximate_cardinality: int | None = None


class ParseResult(BaseModel):
    row_count: int
    column_count: int
    columns: list[ColumnMetadata]
    source_settings: SourceSettings
    available_sheets: list[str] = Field(default_factory=list)
    selected_sheet: str | None = None
    warnings: list[str] = Field(default_factory=list)
