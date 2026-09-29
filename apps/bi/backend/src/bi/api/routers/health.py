"""Health endpoint."""

from fastapi import APIRouter

from bi.api.schemas.common import HealthResponse
from bi.services import system as system_service

router = APIRouter(tags=["system"])


@router.get("/health", response_model=HealthResponse)
def get_health() -> dict[str, str]:
    return system_service.health_status()
