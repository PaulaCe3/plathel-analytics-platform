"""Central environment configuration for the platform."""

from functools import lru_cache
from pathlib import Path

from pydantic import Field, model_validator
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
    profile_sample_rows: int = Field(default=20000, ge=1, validation_alias="PROFILE_SAMPLE_ROWS")
    heavy_concurrency: int = Field(default=2, ge=1, validation_alias="HEAVY_CONCURRENCY")
    absolute_session_ttl_minutes: int = Field(default=240, ge=1, validation_alias="ABSOLUTE_SESSION_TTL_MINUTES")
    reaper_interval_seconds: float = Field(default=120, ge=0.05, validation_alias="REAPER_INTERVAL_SECONDS")
    uploads_per_hour: int = Field(default=10, ge=1, validation_alias="UPLOADS_PER_HOUR")
    max_active_sessions: int = Field(default=100, ge=1, validation_alias="MAX_ACTIVE_SESSIONS")
    max_sessions_per_ip: int = Field(default=10, ge=1, validation_alias="MAX_SESSIONS_PER_IP")
    trusted_proxy_ips: tuple[str, ...] = ()
    cors_origins: tuple[str, ...] = ()
    max_zip_entries: int = Field(default=1000, ge=1, validation_alias="MAX_ZIP_ENTRIES")
    max_zip_expanded_mb: int = Field(default=100, ge=1, validation_alias="MAX_ZIP_EXPANDED_MB")
    max_zip_ratio: float = Field(default=100, ge=1, validation_alias="MAX_ZIP_RATIO")
    multipart_overhead_bytes: int = Field(default=65536, ge=1024, validation_alias="MULTIPART_OVERHEAD_BYTES")
    allowed_extensions: tuple[str, ...] = (".csv", ".xlsx")
    languages: tuple[str, ...] = ("es",)

    @model_validator(mode="after")
    def restricted_origins(self):
        if "*" in (self.cors_origins or (self.frontend_origin,)):
            raise ValueError("CORS requires explicit origins")
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
