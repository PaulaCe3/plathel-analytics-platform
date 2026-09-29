"""System-level services for health and public runtime metadata."""

from analytics_core.settings import Settings


def health_status() -> dict[str, str]:
    return {"status": "ok"}


def application_meta(settings: Settings) -> dict[str, object]:
    return {
        "max_file_mb": settings.max_file_mb,
        "max_rows": settings.max_rows,
        "max_columns": settings.max_columns,
        "ttl_minutes": settings.dataset_ttl_minutes,
        "allowed_extensions": list(settings.allowed_extensions),
        "default_locale": settings.default_locale,
        "languages": list(settings.languages),
    }
