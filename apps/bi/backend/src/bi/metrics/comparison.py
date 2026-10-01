"""Calendar-aware temporal comparison resolution."""

import calendar
import math
from datetime import date, timedelta

from analytics_core.engine.query import DateCoverage
from bi.metrics.models import ComparisonMode, ComparisonResult, DateRange, MetricWarning


def _month_before(day: date) -> tuple[int, int]:
    return (day.year - 1, 12) if day.month == 1 else (day.year, day.month - 1)


def _calendar_range(mode: ComparisonMode, current: DateRange) -> DateRange | None:
    if mode == "none":
        return None
    if mode == "previous_period":
        # Natural, complete calendar windows retain calendar semantics.
        start, end = current.from_date, current.to_date
        months = (end.year-start.year)*12 + end.month-start.month+1
        full_months = start.day == 1 and end.day == calendar.monthrange(end.year,end.month)[1]
        if full_months and months == 1:
            return _calendar_range("previous_month",current)
        if full_months and months == 3 and start.month in (1,4,7,10):
            return _calendar_range("previous_quarter",current)
        if full_months and months == 12 and start.month == 1:
            return _calendar_range("previous_year",current)
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

    def equivalent(self, mode: ComparisonMode, current: DateRange, previous: DateRange) -> bool:
        if current.from_date > current.to_date:
            return False
        natural = _calendar_range("previous_period", current)
        if previous == natural:
            return True
        return (current.to_date-current.from_date).days == (previous.to_date-previous.from_date).days

    def resolve(
        self, mode: ComparisonMode, current_range: DateRange, coverage: DateCoverage,
        current_value: float | int | None, previous_value: float | int | None,
        *, today: date | None = None, percentage_metric: bool = False,
    ) -> ComparisonResult:
        previous = self.previous_range(mode, current_range)
        partial = current_range.to_date >= (today or date.today()) or self.coverage_ratio(current_range,coverage)<0.80
        base = dict(mode=mode, current_range=current_range, previous_range=previous, partial_period=partial)
        if mode == "none" or previous is None:
            return ComparisonResult(**base, status="not_applicable",reason_key="comparison.disabled")
        if not self.equivalent(mode,current_range,previous):
            return ComparisonResult(**base,status="not_applicable",reason_key="comparison.unequal_periods")
        ratio = self.coverage_ratio(previous, coverage)
        if ratio < 0.30 or current_value is None or previous_value is None:
            return ComparisonResult(**base,status="insufficient_data",reason_key="comparison.insufficient_data")
        if not all(math.isfinite(float(value)) for value in (current_value,previous_value)):
            return ComparisonResult(**base,status="insufficient_data",reason_key="comparison.invalid_value")
        warnings = []
        if ratio < 0.80:
            warnings.append(MetricWarning(code="PARTIAL_PREVIOUS_PERIOD",message_key="warning.partial_previous_period"))
        if partial:
            warnings.append(MetricWarning(code="PARTIAL_CURRENT_PERIOD",message_key="warning.partial_current_period"))
        delta = float(current_value)-float(previous_value)
        percentage = None if previous_value == 0 or percentage_metric else delta/abs(float(previous_value))
        pp = delta*100 if percentage_metric else None
        if not math.isfinite(delta) or (percentage is not None and not math.isfinite(percentage)) or (pp is not None and not math.isfinite(pp)):
            return ComparisonResult(**base,status="insufficient_data",reason_key="comparison.invalid_value")
        return ComparisonResult(**base,status="previous_zero" if previous_value == 0 else "ok",previous_value=float(previous_value),delta_abs=delta,delta_pct=percentage,delta_pp=pp,direction="increase" if delta>0 else "decrease" if delta<0 else "unchanged",percentage_reason_key="comparison.percentage_points" if percentage_metric else "comparison.previous_zero" if previous_value == 0 else None,warnings=warnings)
