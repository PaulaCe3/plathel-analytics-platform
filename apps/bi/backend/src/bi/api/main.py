"""FastAPI application factory for BI Multi-Industria."""

import asyncio
from contextlib import asynccontextmanager, suppress
from analytics_core.runtime import RuntimeGuard
from analytics_core.sessions.store import DatasetSessionStore
from fastapi import APIRouter, FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware

from analytics_core.errors import AppError
from analytics_core.logging import configure_logging
from analytics_core.settings import Settings, get_settings
from bi.api.error_handlers import app_error_handler, unexpected_error_handler, request_validation_error_handler
from bi.api.schemas.common import ErrorResponse
from bi.api.middleware import RequestContextMiddleware, RuntimeLimitMiddleware, UploadBodyLimitMiddleware
from bi.api.routers import dashboard, datasets, demos, exports, health, mapping, meta, prepare, profiles


def create_app(settings: Settings | None = None) -> FastAPI:
    resolved = settings or get_settings()
    configure_logging()

    runtime = RuntimeGuard(resolved)

    @asynccontextmanager
    async def lifespan(app):
        store = DatasetSessionStore(resolved.dataset_storage_path, resolved.dataset_ttl_minutes, resolved.absolute_session_ttl_minutes)
        await asyncio.to_thread(store.purge_expired)
        async def reap():
            while True:
                await asyncio.sleep(resolved.reaper_interval_seconds)
                await asyncio.to_thread(store.purge_expired)
                runtime.prune()
        task = asyncio.create_task(reap())
        try:
            yield
        finally:
            task.cancel()
            with suppress(asyncio.CancelledError): await task

    app = FastAPI(
        lifespan=lifespan,
        responses={code: {"model": ErrorResponse} for code in (400, 404, 409, 410, 413, 415, 422, 429, 500, 503)},
        title=resolved.app_name,
        version="0.1.0",
        description="API de ingesta para BI Multi-Industria.",
        openapi_url=f"{resolved.api_prefix}/openapi.json",
        docs_url=f"{resolved.api_prefix}/docs",
        redoc_url=f"{resolved.api_prefix}/redoc",
    )
    app.state.runtime = runtime
    app.state.settings = resolved
    app.add_middleware(UploadBodyLimitMiddleware, settings=resolved)
    app.add_middleware(RuntimeLimitMiddleware)
    app.add_exception_handler(AppError, app_error_handler)
    app.add_exception_handler(RequestValidationError, request_validation_error_handler)
    app.add_exception_handler(Exception, unexpected_error_handler)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=list(resolved.cors_origins or (resolved.frontend_origin,)),
        allow_credentials=False,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["Content-Type", "Accept", "Accept-Language", "X-Request-ID"],
        expose_headers=["Content-Disposition", "X-Request-ID"],
    )
    app.add_middleware(RequestContextMiddleware)
    app.dependency_overrides[get_settings] = lambda: resolved

    api = APIRouter(prefix=resolved.api_prefix)
    api.include_router(health.router)
    api.include_router(meta.router)
    api.include_router(demos.router)
    api.include_router(datasets.router)
    api.include_router(mapping.router)
    api.include_router(profiles.router)
    api.include_router(prepare.router)
    api.include_router(dashboard.router)
    api.include_router(exports.router)
    app.include_router(api)
    return app


app = create_app()
