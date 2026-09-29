"""Thin HTTP endpoints for validation and confirmed cleaning."""

from fastapi import APIRouter
from starlette.concurrency import run_in_threadpool

from bi.api.deps import PrepareServiceDep
from bi.api.schemas.prepare import CleaningRequest, CleaningResponse, ValidateResponse
from analytics_core.cleaning.models import TransformationLog

router = APIRouter(prefix="/datasets", tags=["preparation"])


@router.post("/{dataset_id}/validate", response_model=ValidateResponse)
async def validate_dataset(dataset_id: str, service: PrepareServiceDep) -> ValidateResponse:
    session, validation, quality = await run_in_threadpool(service.validate, dataset_id)
    return ValidateResponse(dataset_id=dataset_id, stage=session.stage, validation=validation, quality=quality, cleaning_plan=session.cleaning_plan, warnings=session.warnings)


@router.put("/{dataset_id}/cleaning", response_model=CleaningResponse)
async def clean_dataset(dataset_id: str, request: CleaningRequest, service: PrepareServiceDep) -> CleaningResponse:
    session, quality = await run_in_threadpool(service.clean, dataset_id, request.actions)
    return CleaningResponse(dataset_id=dataset_id, stage=session.stage, validation=session.validation_report, quality=quality, transformation_log=session.transformation_log, canonical_row_count=session.canonical_row_count or 0)


@router.get("/{dataset_id}/transformations", response_model=TransformationLog)
async def get_transformations(dataset_id: str, service: PrepareServiceDep) -> TransformationLog:
    return await run_in_threadpool(service.transformations, dataset_id)
