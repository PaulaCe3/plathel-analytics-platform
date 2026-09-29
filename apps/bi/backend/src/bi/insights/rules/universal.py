"""Universal, industry-neutral insight rules."""

from bi.insights.config import CHANNEL_MIN_CATEGORIES, CONCENTRATION_MIN_MEMBERS, GROWTH_MIN_ABS, LEADER_MIN_CATEGORIES, LEADER_MIN_SHARE, PEAK_MIN_PERIODS, QUALITY_MIN_RATIO
from bi.insights.engine import Insight
from bi.metrics.models import ComparisonResult


def growth_vs_previous(comparison: ComparisonResult | None, metric_id: str = "revenue") -> list[Insight]:
    if comparison is None or comparison.status != "ok" or comparison.delta_pct is None or abs(comparison.delta_pct) < GROWTH_MIN_ABS:
        return []
    positive = comparison.delta_pct > 0
    return [Insight(id=f"growth:{metric_id}", rule_id="growth_vs_previous", severity="positive" if positive else "negative", template_key="insight.growth", params={"delta_pct": comparison.delta_pct}, text="insight.growth", metric_id=metric_id, score=abs(comparison.delta_pct))]


def leader_share(points: list[list], dimension: str) -> list[Insight]:
    if len(points) < LEADER_MIN_CATEGORIES or not points or float(points[0][2]) < LEADER_MIN_SHARE:
        return []
    return [Insight(id=f"leader:{dimension}", rule_id="leader_share", severity="neutral", template_key="insight.leader_share", params={"value": points[0][0], "share": points[0][2]}, text="insight.leader_share", dimension=dimension, score=float(points[0][2]))]


def top_n_concentration(points: list[list], dimension: str, top_n: int = 5) -> list[Insight]:
    if len(points) < CONCENTRATION_MIN_MEMBERS:
        return []
    share = sum(float(point[2]) for point in points[:top_n])
    return [Insight(id=f"concentration:{dimension}", rule_id="top_n_concentration", severity="attention", template_key="insight.top_n_concentration", params={"top_n": top_n, "share": share}, text="insight.top_n_concentration", dimension=dimension, score=share)]


def peak_period(points: list[list]) -> list[Insight]:
    if len(points) < PEAK_MIN_PERIODS:
        return []
    peak = max(points, key=lambda point: float(point[1]))
    return [Insight(id="peak:time", rule_id="peak_period", severity="neutral", template_key="insight.peak_period", params={"period": peak[0], "value": peak[1]}, text="insight.peak_period", metric_id="revenue", score=float(peak[1]))]


def channel_dominance(points: list[list]) -> list[Insight]:
    if len(points) < CHANNEL_MIN_CATEGORIES:
        return []
    return [Insight(id="dominance:channel", rule_id="channel_dominance", severity="neutral", template_key="insight.channel_dominance", params={"channel": points[0][0], "share": points[0][2]}, text="insight.channel_dominance", dimension="channel", score=float(points[0][2]))]


def data_quality_alert(issue_count: int, row_count: int) -> list[Insight]:
    ratio = issue_count / row_count if row_count else 0
    if ratio < QUALITY_MIN_RATIO:
        return []
    return [Insight(id="quality:alert", rule_id="data_quality_alert", severity="attention", template_key="insight.data_quality_alert", params={"ratio": ratio, "count": issue_count}, text="insight.data_quality_alert", score=ratio)]
