"""Robust, deterministic anomaly candidates for complete temporal buckets."""
from calendar import monthrange
from datetime import date, timedelta
import math
from statistics import median

from bi.insights.config import (ANOMALY_IQR_MULTIPLIER, ANOMALY_MAX_PER_METRIC,
    ANOMALY_MIN_OBSERVATIONS, ANOMALY_MIN_RELATIVE_DEVIATION,
    ANOMALY_MODIFIED_Z_THRESHOLD, KIND_WEIGHT, MAGNITUDE_WEIGHT, RELEVANCE_WEIGHT)
from bi.insights.engine import Insight


def _quantile(values: list[float], fraction: float) -> float:
    position = (len(values) - 1) * fraction
    lower = int(position)
    upper = min(lower + 1, len(values) - 1)
    weight = position - lower
    return values[lower] * (1 - weight) + values[upper] * weight


def _period_bounds(label: str, grain: str) -> tuple[date, date] | None:
    try:
        if grain == "day":
            start = date.fromisoformat(label)
            return start, start
        if grain == "week":
            start = date.fromisoformat(label)
            return start, start + timedelta(days=6)
        if grain == "month":
            year, month = map(int, label.split("-"))
            return date(year, month, 1), date(year, month, monthrange(year, month)[1])
        if grain == "quarter":
            year, quarter = label.split("Q")
            month = (int(quarter) - 1) * 3 + 1
            end_month = month + 2
            return date(int(year), month, 1), date(int(year), end_month, monthrange(int(year), end_month)[1])
        year = int(label)
        return date(year, 1, 1), date(year, 12, 31)
    except (TypeError, ValueError):
        return None


def _next_period(start: date, grain: str) -> date:
    if grain == "day": return start + timedelta(days=1)
    if grain == "week": return start + timedelta(days=7)
    if grain == "month": return date(start.year + (start.month == 12), start.month % 12 + 1, 1)
    if grain == "quarter":
        month = start.month + 3
        return date(start.year + (month > 12), (month - 1) % 12 + 1, 1)
    return date(start.year + 1, 1, 1)


def _complete_contiguous(points: list[list], grain: str, analysis_end: date, today: date) -> list[tuple[str, float]]:
    parsed = []
    for point in points:
        if len(point) < 2 or point[1] is None:
            return []
        bounds = _period_bounds(str(point[0]), grain)
        try:
            value = float(point[1])
        except (TypeError, ValueError):
            return []
        if bounds is None or not math.isfinite(value):
            return []
        parsed.append((str(point[0]), value, bounds))
    parsed.sort(key=lambda item: item[2][0])
    complete = [(label, value, bounds) for label, value, bounds in parsed
                if bounds[1] <= analysis_end and bounds[1] < today]
    if any(_next_period(left[2][0], grain) != right[2][0] for left, right in zip(complete, complete[1:])):
        return []
    return [(label, value) for label, value, _ in complete]


def anomaly_candidates(profile, metric: str, metric_label: str, points: list[list], grain: str,
                       analysis_end: date, context: list[dict], *, today: date | None = None) -> list[Insight]:
    series = _complete_contiguous(points, grain, analysis_end, today or date.today())
    if len(series) < ANOMALY_MIN_OBSERVATIONS:
        return []
    values = [value for _, value in series]
    baseline = median(values)
    deviations = [abs(value - baseline) for value in values]
    mad = median(deviations)
    sorted_values = sorted(values)
    iqr = _quantile(sorted_values, .75) - _quantile(sorted_values, .25)
    candidates = []
    order = profile.bi.kpi_order if profile.bi else ()
    relevance = 1 / (1 + order.index(metric)) if metric in order else 0
    latest_observed = str(points[-1][0]) if points else None
    for period, observed in series:
        delta = observed - baseline
        relative = abs(delta) / abs(baseline) if baseline else None
        if relative is not None and relative < ANOMALY_MIN_RELATIVE_DEVIATION:
            continue
        if mad > 0:
            magnitude = abs(.6745 * delta / mad)
            if magnitude < ANOMALY_MODIFIED_Z_THRESHOLD:
                continue
            method = "modified_z"
        elif iqr > 0:
            lower = _quantile(sorted_values, .25) - ANOMALY_IQR_MULTIPLIER * iqr
            upper = _quantile(sorted_values, .75) + ANOMALY_IQR_MULTIPLIER * iqr
            if lower <= observed <= upper:
                continue
            magnitude = abs(delta) / iqr
            method = "iqr"
        else:
            continue
        direction = "alto" if delta > 0 else "bajo"
        kind = "anomaly_high" if delta > 0 else "anomaly_low"
        percent = f"{abs(relative)*100:.1f}".replace(".", ",") if relative is not None else None
        detail = f" Fue aproximadamente {percent} % {'mayor' if delta > 0 else 'menor'} que el nivel habitual del período analizado." if percent is not None else ""
        text = f"{period} mostró un nivel inusualmente {direction} de {metric_label.lower()} frente al patrón histórico observado.{detail}"
        normalized_magnitude = min(math.log1p(magnitude / ANOMALY_MODIFIED_Z_THRESHOLD), 3)
        score = KIND_WEIGHT[kind] + RELEVANCE_WEIGHT * relevance + MAGNITUDE_WEIGHT * normalized_magnitude
        candidates.append(Insight(id=f"{kind}:{metric}:{period}", rule_id=kind, kind=kind,
            severity="attention", template_key="business.fact", text=text, metric_id=metric,
            params={"period": period, "observed": observed, "baseline": baseline,
                    "direction": direction, "deviation": delta, "relative_deviation": relative,
                    "technical": {"method": method, "magnitude": magnitude, "observations": len(series)},
                    "filters": context, "latest": period == latest_observed}, score=score))
    return sorted(candidates, key=lambda item: (-item.score, item.id))[:ANOMALY_MAX_PER_METRIC]
