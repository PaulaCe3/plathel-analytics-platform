from pydantic import BaseModel, Field

from analytics_core.cleaning.models import CleaningActionSpec, CleaningPlan, TransformationLog
from analytics_core.quality.models import DataQualityReport
from analytics_core.validation.models import ValidationReport


class ValidateResponse(BaseModel):
    dataset_id: str
    stage: str
    validation: ValidationReport
    quality: DataQualityReport
    cleaning_plan: CleaningPlan
    warnings: list[str] = Field(default_factory=list)


class CleaningRequest(BaseModel):
    actions: list[CleaningActionSpec]


class CleaningResponse(BaseModel):
    dataset_id: str
    stage: str
    validation: ValidationReport
    quality: DataQualityReport
    transformation_log: TransformationLog
    canonical_row_count: int
