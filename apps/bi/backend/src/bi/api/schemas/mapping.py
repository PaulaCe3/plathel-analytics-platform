from pydantic import BaseModel

from analytics_core.ingestion.models import ColumnMetadata
from analytics_core.mapping.models import ColumnMapping, MappingConflict, MappingSuggestion
from bi.api.schemas.profiles import ProfileResponse


class MappingRequest(BaseModel):
    profile_id: str
    mappings: list[ColumnMapping]


class MappingResponse(BaseModel):
    dataset_id: str
    stage: str
    profile: ProfileResponse
    columns: list[ColumnMetadata]
    suggestions: list[MappingSuggestion]
    mappings: list[ColumnMapping]
    conflicts: list[MappingConflict]
    unmapped_columns: list[str]
