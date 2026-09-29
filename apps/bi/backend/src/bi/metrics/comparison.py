"""Calendar-aware temporal comparison resolution."""

import calendar
from datetime import date, timedelta

from analytics_core.engine.query import DateCoverage
from bi.metrics.models import ComparisonMode, ComparisonResult, DateRange, MetricWarning


def _month_before(day: date) -> tuple[int, int]:
    return (day.year - 1, 12) if day.month == 1 else (day.year, day.month - 1)


def _calendar_range(mode: ComparisonMode, current: DateRange) -> DateRange | None:
    if mode == "none":
        return None
    if mode == "previous_period":
        days = (current.to_date - current.from_date).days + 1
        end = current.from_date - timedelta(days=1)
        return DateRange(from_date=end - timedelta(days=days - 1), to_date=end)
    if mode == "previous_week":
        start_this_week = current.from_date - timedelta(days=current.from_date.weekday())
        end = start_this_week - timedelta(days=1)
        return DateRange(from_date=end - timedelta(days=6), to_date=end)
    if mode == "previous_month":
        year, month = _month_before(current.from_date)
        return DateRange(from_date=date(year, month, 1), to_date=date(year, month, calendar.monthrange(year, month)[1]))
    if mode == "previous_quarter":
        quarter_start_month = ((current.from_date.month - 1) // 3) * 3 + 1
        this_start = date(current.from_date.year, quarter_start_month, 1)
        prior_end = this_start - timedelta(days=1)
        prior_start_month = ((prior_end.month - 1) // 3) * 3 + 1
        return DateRange(from_date=date(prior_end.year, prior_start_month, 1), to_date=prior_end)
    year = current.from_date.year - 1
    return DateRange(from_date=date(year, 1, 1), to_date=date(year, 12, 31))


class ComparisonResolver:
    def previous_range(self, mode: ComparisonMode, current: DateRange) -> DateRange | None:
        return _calendar_range(mode, current)

    def coverage_ratio(self, requested: DateRange, coverage: DateCoverage) -> float:
        if coverage.minimum is None or coverage.maximum is None:
            return 0.0
        overlap_start = max(requested.from_date, coverage.minimum)
        overlap_end = min(requested.to_date, coverage.maximum)
        if overlap_end < overlap_start:
            return 0.0
        covered = (overlap_end - overlap_start).days + 1
        requested_days = (requested.to_date - requested.from_date).days + 1
        return covered / requested_days if requested_days > 0 else 0.0

    def resolve(
        self,
        mode: ComparisonMode,
        current_range: DateRange,
        coverage: DateCoverage,
        current_value: float | int | None,
        previous_value: float | int | None,
        *,
        today: date | None = None,
    ) -> ComparisonResult:
        previous = self.previous_range(mode, current_range)
        if mode == "none" or previous is None:
            return ComparisonResult(mode=mode, status="not_applicable")
        partial = current_range.to_date >= (today or date.today())
        ratio = self.coverage_ratio(previous, coverage)
        if ratio < 0.30 or current_value is None or previous_value is None:
            return ComparisonResult(mode=mode, status="insufficient_data", previous_range=previous, partial_period=partial)
        warnings = []
        if ratio < 0.80:
            warnings.append(MetricWarning(code="PARTIAL_PREVIOUS_PERIOD", message_key="warning.partial_previous_period"))
        delta = float(current_value) - float(previous_value)
        if float(previous_value) == 0:
            return ComparisonResult(mode=mode, status="previous_zero", previous_value=float(previous_value), delta_abs=delta, delta_pct=None, previous_range=previous, partial_period=partial, warnings=warnings)
        return ComparisonResult(mode=mode, status="ok", previous_value=float(previous_value), delta_abs=delta, delta_pct=delta / float(previous_value), previous_range=previous, partial_period=partial, warnings=warnings)
