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
    kind: Literal["change", "leadership", "concentration", "segment_change", "contribution", "divergence", "anomaly_high", "anomaly_low"] | None = None
    score: float


class InsightEngine:
    def prioritize(self, insights: list[Insight], limit: int = SECTION_LIMIT) -> list[Insight]:
        anomalous_latest = {item.metric_id for item in insights
                            if item.kind in {"anomaly_high", "anomaly_low"} and item.params.get("latest")}
        insights = [item for item in insights
                    if not (item.kind == "change" and item.metric_id in anomalous_latest)]
        unique: dict[tuple, Insight] = {}
        for insight in insights:
            key = (insight.kind or insight.rule_id, insight.metric_id, insight.dimension, insight.params.get("segment"))
            if key not in unique or insight.score > unique[key].score:
                unique[key] = insight
        return sorted(unique.values(), key=lambda item: (-item.score, item.id))[:limit]
