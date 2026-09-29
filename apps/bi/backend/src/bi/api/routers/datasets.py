"""Thin HTTP boundary for temporary datasets."""

from typing import Annotated

from fastapi import APIRouter, File, Form, Query, Response, UploadFile, status
from starlette.concurrency import run_in_threadpool

from analytics_core.ingestion.models import SourceSettings
from bi.api.deps import DatasetServiceDep, SettingsDep
from bi.api.schemas.datasets import DatasetPatch, DatasetResponse, PreviewResponse

router = APIRouter(prefix="/datasets", tags=["datasets"])


@router.post("", response_model=DatasetResponse, status_code=status.HTTP_201_CREATED)
async def create_dataset(
    service: DatasetServiceDep,
    file: Annotated[UploadFile, File(...)],
    industry_id: Annotated[str | None, Form()] = None,
) -> DatasetResponse:
    session = await run_in_threadpool(service.create, file.file, file.filename or "", industry_id)
    return DatasetResponse.model_validate(session, from_attributes=True)


@router.get("/{dataset_id}", response_model=DatasetResponse)
async def get_dataset(dataset_id: str, service: DatasetServiceDep) -> DatasetResponse:
    session = await run_in_threadpool(service.get, dataset_id)
    return DatasetResponse.model_validate(session, from_attributes=True)


@router.get("/{dataset_id}/preview", response_model=PreviewResponse)
async def get_preview(
    dataset_id: str,
    service: DatasetServiceDep,
    settings: SettingsDep,
    rows: Annotated[int | None, Query(ge=1)] = None,
) -> PreviewResponse:
    limited_rows = min(rows or settings.preview_default_rows, settings.preview_max_rows)
    session, data = await run_in_threadpool(service.preview, dataset_id, limited_rows)
    return PreviewResponse(
        dataset_id=session.dataset_id,
        row_count=session.row_count,
        column_count=session.column_count,
        selected_sheet=session.selected_sheet,
        columns=session.columns,
        rows=data,
        warnings=session.warnings,
    )


@router.patch("/{dataset_id}", response_model=DatasetResponse)
async def update_dataset(dataset_id: str, patch: DatasetPatch, service: DatasetServiceDep) -> DatasetResponse:
    if patch.industry_id is not None:
        session = await run_in_threadpool(service.change_industry, dataset_id, patch.industry_id)
    else:
        session = await run_in_threadpool(service.update_source, dataset_id, SourceSettings(**patch.model_dump(exclude_unset=True)))
    return DatasetResponse.model_validate(session, from_attributes=True)


@router.delete("/{dataset_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_dataset(dataset_id: str, service: DatasetServiceDep) -> Response:
    await run_in_threadpool(service.delete, dataset_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
