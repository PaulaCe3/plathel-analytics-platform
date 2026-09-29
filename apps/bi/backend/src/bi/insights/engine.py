"""Deterministic insight orchestration, scoring and deduplication."""

from typing import Any, Literal
from pydantic import BaseModel

from bi.insights.config import SECTION_LIMIT


class Insight(BaseModel, frozen=True):
    id: str
    rule_id: str
    severity: Literal["positive", "negative", "neutral", "attention"]
    template_key: str
    params: dict[str, Any]
    text: str
    metric_id: str | None = None
    dimension: str | None = None
    score: float


class InsightEngine:
    def prioritize(self, insights: list[Insight], limit: int = SECTION_LIMIT) -> list[Insight]:
        unique: dict[tuple[str, str | None], Insight] = {}
        for insight in insights:
            key = (insight.rule_id, insight.dimension)
            if key not in unique or insight.score > unique[key].score:
                unique[key] = insight
        return sorted(unique.values(), key=lambda item: (-item.score, item.id))[:limit]
