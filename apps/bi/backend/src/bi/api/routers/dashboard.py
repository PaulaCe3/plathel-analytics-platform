"""Thin dashboard and filter-option endpoints."""

from fastapi import APIRouter, Query
from starlette.concurrency import run_in_threadpool

from bi.api.deps import DashboardServiceDep
from bi.api.schemas.dashboard import DashboardRequest, DashboardResponse, FilterOptionsResponse

router = APIRouter(prefix="/datasets", tags=["dashboard"])


@router.post("/{dataset_id}/dashboard", response_model=DashboardResponse)
async def dashboard(dataset_id: str, request: DashboardRequest, service: DashboardServiceDep) -> DashboardResponse:
    return await run_in_threadpool(service.dashboard, dataset_id, request)


@router.get("/{dataset_id}/filters/{field}/options", response_model=FilterOptionsResponse)
async def filter_options(dataset_id: str, field: str, service: DashboardServiceDep, q: str | None = None, limit: int = Query(default=50, ge=1, le=100)) -> FilterOptionsResponse:
    options = await run_in_threadpool(service.filter_options, dataset_id, field, q, limit)
    return FilterOptionsResponse(field=field, options=options)
