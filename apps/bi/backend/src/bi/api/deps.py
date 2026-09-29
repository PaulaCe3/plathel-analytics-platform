"""Shared FastAPI dependencies."""

from typing import Annotated

from fastapi import Depends

from analytics_core.settings import Settings, get_settings
from bi.services.datasets import DatasetService
from bi.services.mapping import MappingService
from bi.services.profiles import ProfileService

SettingsDep = Annotated[Settings, Depends(get_settings)]


def get_dataset_service(settings: SettingsDep) -> DatasetService:
    return DatasetService(settings)


DatasetServiceDep = Annotated[DatasetService, Depends(get_dataset_service)]


def get_mapping_service(settings: SettingsDep) -> MappingService:
    return MappingService(settings)


MappingServiceDep = Annotated[MappingService, Depends(get_mapping_service)]
ProfileServiceDep = Annotated[ProfileService, Depends(ProfileService)]
