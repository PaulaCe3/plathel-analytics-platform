"""Public configuration exposed to the frontend."""

from pydantic import BaseModel


class MetaResponse(BaseModel):
    max_file_mb: int
    max_rows: int
    max_columns: int
    ttl_minutes: int
    allowed_extensions: list[str]
    default_locale: str
    languages: list[str]
