"""Shared FastAPI dependencies."""

from typing import Annotated

from fastapi import Depends

from analytics_core.settings import Settings, get_settings
from bi.services.datasets import DatasetService
from bi.services.mapping import MappingService
from bi.services.profiles import ProfileService
from bi.services.prepare import PrepareService
from bi.services.dashboard import DashboardService
from bi.services.exports import ExportService
from bi.services.demos import DemoService

SettingsDep = Annotated[Settings, Depends(get_settings)]


def get_dataset_service(settings: SettingsDep) -> DatasetService:
    return DatasetService(settings)


DatasetServiceDep = Annotated[DatasetService, Depends(get_dataset_service)]


def get_mapping_service(settings: SettingsDep) -> MappingService:
    return MappingService(settings)


MappingServiceDep = Annotated[MappingService, Depends(get_mapping_service)]
ProfileServiceDep = Annotated[ProfileService, Depends(ProfileService)]


def get_prepare_service(settings: SettingsDep) -> PrepareService:
    return PrepareService(settings)


PrepareServiceDep = Annotated[PrepareService, Depends(get_prepare_service)]


def get_dashboard_service(settings: SettingsDep) -> DashboardService:
    return DashboardService(settings)


DashboardServiceDep = Annotated[DashboardService, Depends(get_dashboard_service)]


def get_export_service(settings: SettingsDep) -> ExportService:
    return ExportService(settings)


ExportServiceDep = Annotated[ExportService, Depends(get_export_service)]


def get_demo_service(settings: SettingsDep) -> DemoService:
    return DemoService(settings)


DemoServiceDep = Annotated[DemoService, Depends(get_demo_service)]
