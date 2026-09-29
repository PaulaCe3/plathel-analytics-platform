"""Central environment configuration for the platform."""

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    app_name: str = Field(default="BI Multi-Industria", validation_alias="APP_NAME")
    app_env: str = Field(default="development", validation_alias="APP_ENV")
    api_prefix: str = Field(default="/api/v1", validation_alias="API_PREFIX")
    default_locale: str = Field(default="es-AR", validation_alias="DEFAULT_LOCALE")
    frontend_origin: str = Field(
        default="http://localhost:3000", validation_alias="FRONTEND_ORIGIN"
    )
    max_file_mb: int = Field(default=20, ge=1, validation_alias="MAX_FILE_MB")
    max_rows: int = Field(default=250_000, ge=1, validation_alias="MAX_ROWS")
    max_columns: int = Field(default=200, ge=1, validation_alias="MAX_COLUMNS")
    dataset_ttl_minutes: int = Field(
        default=60, ge=1, validation_alias="DATASET_TTL_MINUTES"
    )
    dataset_storage_path: Path = Field(
        default=Path(".data/sessions"), validation_alias="DATASET_STORAGE_PATH"
    )
    preview_default_rows: int = Field(
        default=50, ge=1, le=200, validation_alias="PREVIEW_DEFAULT_ROWS"
    )
    preview_max_rows: int = Field(
        default=100, ge=1, le=500, validation_alias="PREVIEW_MAX_ROWS"
    )
    max_custom_dimensions: int = Field(default=10, ge=0, validation_alias="MAX_CUSTOM_DIMENSIONS")
    max_custom_measures: int = Field(default=5, ge=0, validation_alias="MAX_CUSTOM_MEASURES")
    allowed_extensions: tuple[str, ...] = (".csv", ".xlsx")
    languages: tuple[str, ...] = ("es",)


@lru_cache
def get_settings() -> Settings:
    return Settings()
