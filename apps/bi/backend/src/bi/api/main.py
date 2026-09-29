"""FastAPI application factory for BI Multi-Industria."""

from fastapi import APIRouter, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from analytics_core.errors import AppError
from analytics_core.logging import configure_logging
from analytics_core.settings import Settings, get_settings
from bi.api.error_handlers import app_error_handler, unexpected_error_handler
from bi.api.middleware import RequestContextMiddleware
from bi.api.routers import datasets, health, mapping, meta, prepare, profiles


def create_app(settings: Settings | None = None) -> FastAPI:
    resolved = settings or get_settings()
    configure_logging()

    app = FastAPI(
        title=resolved.app_name,
        version="0.1.0",
        description="API de ingesta para BI Multi-Industria.",
        openapi_url=f"{resolved.api_prefix}/openapi.json",
        docs_url=f"{resolved.api_prefix}/docs",
        redoc_url=f"{resolved.api_prefix}/redoc",
    )
    app.add_exception_handler(AppError, app_error_handler)
    app.add_exception_handler(Exception, unexpected_error_handler)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[resolved.frontend_origin],
        allow_credentials=True,
        allow_methods=["GET", "POST", "PATCH", "DELETE"],
        allow_headers=["*"],
    )
    app.add_middleware(RequestContextMiddleware)
    app.dependency_overrides[get_settings] = lambda: resolved

    api = APIRouter(prefix=resolved.api_prefix)
    api.include_router(health.router)
    api.include_router(meta.router)
    api.include_router(datasets.router)
    api.include_router(mapping.router)
    api.include_router(profiles.router)
    api.include_router(prepare.router)
    app.include_router(api)
    return app


app = create_app()
