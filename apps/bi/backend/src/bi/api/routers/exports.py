"""Format-independent export endpoint; all orchestration lives in the service."""
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from starlette.concurrency import run_in_threadpool
from bi.api.deps import ExportServiceDep
from bi.api.schemas.exports import ExportRequest

router = APIRouter(prefix="/datasets", tags=["exports"])


@router.post("/{dataset_id}/export", response_class=StreamingResponse)
async def export_dataset(dataset_id: str, request: ExportRequest, service: ExportServiceDep):
    prepared = await run_in_threadpool(service.prepare, dataset_id, request)
    return StreamingResponse(prepared.chunks, media_type=prepared.content_type, headers={"Content-Disposition": f'attachment; filename="{prepared.filename}"', "Cache-Control": "no-store"})
