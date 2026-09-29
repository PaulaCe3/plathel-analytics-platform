"""Public application metadata endpoint."""

from fastapi import APIRouter

from bi.api.deps import SettingsDep
from bi.api.schemas.meta import MetaResponse
from bi.services import system as system_service

router = APIRouter(tags=["system"])


@router.get("/meta", response_model=MetaResponse)
def get_meta(settings: SettingsDep) -> dict[str, object]:
    return system_service.application_meta(settings)
