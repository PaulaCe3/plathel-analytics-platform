"""Public configuration exposed to the frontend."""

from pydantic import BaseModel


class MetaResponse(BaseModel):
    max_file_mb: int
    max_rows: int
    max_columns: int
    ttl_minutes: int
    absolute_ttl_minutes: int
    preview_rows: int
    allowed_extensions: list[str]
    default_locale: str
    languages: list[str]
