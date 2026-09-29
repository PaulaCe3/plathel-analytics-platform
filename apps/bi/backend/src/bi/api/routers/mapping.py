"""Thin HTTP boundary for mapping suggestions and confirmation."""

from fastapi import APIRouter
from starlette.concurrency import run_in_threadpool

from bi.api.deps import MappingServiceDep
from bi.api.routers.profiles import public_profile
from bi.api.schemas.mapping import MappingRequest, MappingResponse

router = APIRouter(prefix="/datasets", tags=["mapping"])


def response_from_view(view) -> MappingResponse:
    session, profile, _fields, suggestions, conflicts, unmapped = view
    return MappingResponse(dataset_id=session.dataset_id, stage=session.stage, profile=public_profile(profile), columns=session.columns, suggestions=suggestions, mappings=session.mappings, conflicts=conflicts, unmapped_columns=unmapped)


@router.get("/{dataset_id}/mapping", response_model=MappingResponse)
async def get_mapping(dataset_id: str, service: MappingServiceDep) -> MappingResponse:
    return response_from_view(await run_in_threadpool(service.view, dataset_id))


@router.put("/{dataset_id}/mapping", response_model=MappingResponse)
async def put_mapping(dataset_id: str, request: MappingRequest, service: MappingServiceDep) -> MappingResponse:
    await run_in_threadpool(service.save, dataset_id, request.profile_id, request.mappings)
    return response_from_view(await run_in_threadpool(service.view, dataset_id))
