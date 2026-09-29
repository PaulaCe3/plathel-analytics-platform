"""Quality findings; deliberately no numeric score."""

from pydantic import BaseModel, Field

from analytics_core.validation.models import Issue


class QualitySummary(BaseModel):
    total_issues: int = 0
    error_count: int = 0
    warning_count: int = 0
    info_count: int = 0
    categories: dict[str, int] = Field(default_factory=dict)


class DataQualityReport(BaseModel):
    issues: list[Issue] = Field(default_factory=list)
    summary: QualitySummary = Field(default_factory=QualitySummary)


def quality_report(issues: list[Issue]) -> DataQualityReport:
    categories: dict[str, int] = {}
    for issue in issues:
        categories[issue.category] = categories.get(issue.category, 0) + 1
    return DataQualityReport(
        issues=issues,
        summary=QualitySummary(
            total_issues=len(issues),
            error_count=sum(issue.severity == "error" for issue in issues),
            warning_count=sum(issue.severity == "warning" for issue in issues),
            info_count=sum(issue.severity == "info" for issue in issues),
            categories=categories,
        ),
    )
