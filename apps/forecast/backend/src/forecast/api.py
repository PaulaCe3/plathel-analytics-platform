"""Thin product endpoints, composed with the existing protected runtime."""
from typing import Annotated
from fastapi import APIRouter, Depends, Request
from starlette.concurrency import run_in_threadpool
from forecast.models import ForecastOptions, ForecastRequest, ForecastResult
from forecast.service import ForecastService

router = APIRouter(prefix="/forecast/datasets", tags=["forecast"])

def service(request: Request):
    return ForecastService(request.app.state.settings, request.app.state.runtime)

Service = Annotated[ForecastService, Depends(service)]

@router.get("/{dataset_id}/options", response_model=ForecastOptions)
async def options(dataset_id: str, service: Service):
    return await run_in_threadpool(service.options, dataset_id)

@router.post("/{dataset_id}/prediction", response_model=ForecastResult)
async def prediction(dataset_id: str, request: ForecastRequest, service: Service):
    return await run_in_threadpool(service.predict, dataset_id, request)
