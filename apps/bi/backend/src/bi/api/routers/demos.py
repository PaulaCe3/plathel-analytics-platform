"""Public demo catalog and session creation."""
from fastapi import APIRouter, status
from starlette.concurrency import run_in_threadpool
from bi.api.deps import DemoServiceDep
from bi.api.schemas.demos import DemoRequest, DemoSummary
from bi.api.schemas.datasets import DatasetResponse

router = APIRouter(tags=["demos"])


@router.get("/demos", response_model=list[DemoSummary])
async def list_demos(service: DemoServiceDep):
    return await run_in_threadpool(service.list)


@router.post("/datasets/demo", response_model=DatasetResponse, status_code=status.HTTP_201_CREATED)
async def create_demo(request: DemoRequest, service: DemoServiceDep):
    session = await run_in_threadpool(service.create, request.demo_id)
    return DatasetResponse.model_validate(session, from_attributes=True)
