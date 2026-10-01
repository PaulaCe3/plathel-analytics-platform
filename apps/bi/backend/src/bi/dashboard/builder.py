"""Resolve config and execute isolated dashboard widgets."""

from datetime import date, datetime, time
from pathlib import Path
from typing import Any

from analytics_core.engine.base import DataEngine
from analytics_core.engine.query import FilterClause, GroupBy, MeasureSpec, QuerySpec
from bi.dashboard.filters import derive_filters
from bi.dashboard.templates import LayoutSpec, SectionTemplate, WidgetTemplate
from bi.dashboard.widgets import ChartResult, ChartSeries, ComparisonOption, DashboardSpec, QualityResult, SectionSpec, WidgetSpec
from bi.insights.engine import InsightEngine
from bi.insights.business import business_insights
from bi.insights.rules.universal import leader_share, peak_period, top_n_concentration
from bi.metrics.availability import resolve_availability
from bi.metrics.comparison import ComparisonResolver
from bi.metrics.engine import MetricEngine
from bi.metrics.models import ComparisonResult, ComparisonSpec, DateRange, MetricResult, UnavailableMetric
from bi.metrics.registry import MetricRegistry


def auto_grain(start: date | None, end: date | None) -> str:
    if not start or not end:
        return "month"
    days = (end - start).days + 1
    return "day" if days <= 62 else "month" if days <= 730 else "quarter"


def _has_nonnegative_points(result):
    points = result.series[0].points if result.series else []
    return bool(points) and all(isinstance(point[1], (int, float)) and point[1] >= 0 and (len(point) < 3 or isinstance(point[2], (int, float))) for point in points)


class DashboardBuilder:
    def __init__(self, engine: DataEngine, metrics: MetricRegistry):
        self.engine = engine
        self.metric_engine = MetricEngine(engine, metrics)
        self.metrics = metrics
        self.comparisons = ComparisonResolver()

    def _templates(self, profile, available: set[str], time_field: str, fields=()) -> list[SectionTemplate]:
        bi = profile.bi
        kpis = tuple(WidgetTemplate(id=f"kpi_{metric}", type="kpi", title_key=f"metric.{metric}", metric_id=metric, layout=LayoutSpec(span=3)) for metric in (bi.kpi_order if bi else ())[:6])
        sections = [SectionTemplate(id="executive_summary", title_key="section.executive_summary", widgets=(*kpis, WidgetTemplate(id="insights_top", type="insights", title_key="section.insights", layout=LayoutSpec(span=12))))]
        if time_field in available:
            sections.append(SectionTemplate(id="temporal", title_key="section.temporal", visible_if_fields=(time_field,), widgets=(WidgetTemplate(id="revenue_over_time", type="timeseries", title_key="metric.revenue", metric_id="revenue", required_fields=(time_field, "amount"), layout=LayoutSpec(span=12)),)))
        dimensions = list(bi.featured_dimensions if bi else ())
        custom_dimensions = {field.id for field in fields if field.scope == "custom" and field.kind == "dimension"}
        dimensions.extend(sorted(field for field in custom_dimensions if field in available and field not in dimensions))
        generic = [field for field in dimensions if field in available and field not in {"concept", "customer_id", "customer_name", "location", "channel"}]
        if generic:
            sections.append(SectionTemplate(id="breakdown", title_key="section.breakdown", widgets=tuple(WidgetTemplate(id=f"revenue_by_{dim}", type="breakdown", title_key=f"field.{dim}", metric_id="revenue", dimension=dim, top_n=10, chart_variant="bar", required_fields=("amount", dim)) for dim in generic)))
        conditional = (("customers", "customer_id" if "customer_id" in available else "customer_name"), ("concept_analysis", "concept"), ("geography", "location"), ("channel", "channel"))
        for section_id, dim in conditional:
            if dim in available:
                sections.append(SectionTemplate(id=section_id, title_key=f"section.{section_id}", widgets=(WidgetTemplate(id=f"revenue_by_{dim}", type="ranking" if section_id in {"customers", "geography"} else "breakdown", title_key=f"field.{dim}", metric_id="revenue", dimension=dim, top_n=10, chart_variant="donut" if section_id == "channel" else "bar", required_fields=("amount", dim)),)))
        if {"amount", "cost"} <= available:
            sections.append(SectionTemplate(id="profitability", title_key="section.profitability"))
        custom = sorted(custom_dimensions & available)
        if custom:
            sections.append(SectionTemplate(id="custom_dimensions", title_key="section.custom_dimensions", widgets=tuple(WidgetTemplate(id=f"revenue_by_{dim}", type="breakdown", title_key=dim, metric_id="revenue", dimension=dim, top_n=10, required_fields=("amount", dim)) for dim in custom)))
        if bi and bi.widgets:
            sections.append(SectionTemplate(id="industry_specific", title_key="section.industry_specific", widgets=tuple(WidgetTemplate(**widget.model_dump()) for widget in bi.widgets)))
        sections.append(SectionTemplate(id="data_quality", title_key="section.data_quality", widgets=(WidgetTemplate(id="quality", type="quality", title_key="section.data_quality", layout=LayoutSpec(span=12)),)))
        return sections

    def build(self, *, profile, canonical_path: Path, fields: list, available: set[str], filters: list[FilterClause], comparison: ComparisonSpec, time_field: str, grain: str, quality, row_count: int) -> tuple[DashboardSpec, dict[str, Any], int, list[dict]]:
        enabled = set(profile.bi.metrics if profile.bi else ()) & {metric.id for metric in self.metrics.all()}
        availability = resolve_availability(self.metrics, available)
        unavailable = [UnavailableMetric(metric_id=metric.id, label_key=metric.label_key, missing_fields=availability[metric.id].missing_fields, reason_key=availability[metric.id].reason_key) for metric in self.metrics.all() if metric.id in enabled and not availability[metric.id].available]
        coverage = self.engine.date_coverage(canonical_path, time_field) if time_field in available else None
        current_range = self._current_range(filters, time_field, coverage)
        resolved_grain = auto_grain(current_range.from_date, current_range.to_date) if grain == "auto" and current_range else ("month" if grain == "auto" else grain)
        previous_range = self.comparisons.previous_range(comparison.mode,current_range) if current_range else None
        counts = None
        if comparison.mode != "none" and previous_range and coverage and self.comparisons.equivalent(comparison.mode,current_range,previous_range) and self.comparisons.coverage_ratio(previous_range,coverage)>=0.30:
            previous_filters = self._previous_filters(filters,time_field,previous_range)
            query = lambda clauses: int(self.engine.run_query(canonical_path,QuerySpec(measures=[MeasureSpec(alias="rows",aggregation="count")],filters=clauses)).rows[0]["rows"])
            counts = (query(filters),query(previous_filters))
        data: dict[str, Any] = {}
        sections: list[SectionSpec] = []
        chart_points: dict[str, list[list]] = {}
        warnings: list[dict] = []
        for section in self._templates(profile, available, time_field, fields):
            if not set(section.visible_if_fields) <= available:
                continue
            widgets: list[WidgetSpec] = []
            for template in section.widgets:
                if (template.dimension and template.dimension not in available) or not set(template.required_fields) <= available or (template.metric_id and (template.metric_id not in enabled or not availability[template.metric_id].available)):
                    continue
                try:
                    result = self._widget(template, canonical_path, available, filters, time_field, resolved_grain, quality)
                    if isinstance(result, MetricResult) and comparison.mode != "none" :
                        result = self._with_comparison(result, template.metric_id or "", canonical_path, available, filters, time_field, comparison, current_range, coverage, counts)
                except Exception:
                    result = ChartResult(status="error", widget_id=template.id, chart="breakdown", x_type="category", error_key="widget.error")
                if getattr(result, "status", None) == "unavailable":
                    unavailable_id = template.metric_id or "revenue"
                    if not any(item.metric_id == unavailable_id for item in unavailable):
                        reason = result.warnings[0].message_key if isinstance(result, MetricResult) and result.warnings else result.meta.get("reason_key") if isinstance(result, ChartResult) else None
                        unavailable.append(UnavailableMetric(metric_id=unavailable_id, label_key=f"metric.{unavailable_id}", missing_fields=[], reason_key=reason))
                    continue
                data[template.id] = result
                if isinstance(result, ChartResult) and result.series:
                    if template.metric_id == "revenue" and _has_nonnegative_points(result):
                        chart_points[template.dimension or "time"] = result.series[0].points
                widgets.append(WidgetSpec(id=template.id, type=template.type, title_key=template.title_key, chart_variant=template.chart_variant, layout=template.layout))
            if widgets:
                sections.append(SectionSpec(id=section.id, title_key=section.title_key, collapsed=section.collapsed, widgets=widgets))
        key_charts = []
        seen_dimensions = set()
        candidates = [widget for section in sections for widget in section.widgets if widget.type in {"timeseries", "breakdown", "ranking"}]
        for widget in sorted(candidates, key=lambda widget: {"timeseries": 0, "breakdown": 1, "ranking": 2}[widget.type]):
            result = data.get(widget.id)
            if not isinstance(result, ChartResult) or result.status != "ok" or not result.series:
                continue
            dimension = "time" if widget.type == "timeseries" else widget.title_key
            if dimension in seen_dimensions:
                continue
            seen_dimensions.add(dimension)
            points = result.series[0].points
            useful = peak_period(points) if widget.type == "timeseries" else (top_n_concentration(points, dimension, top_n=3) + leader_share(points, dimension) if _has_nonnegative_points(result) and all(len(point)>2 and point[2] is not None for point in points) else [])
            interpreted = InsightEngine().prioritize(useful, limit=1)
            data[widget.id] = result.model_copy(update={"interpretation": interpreted[0] if interpreted else None})
            if len(key_charts) < 4 and widget.id not in key_charts:
                key_charts.append(widget.id)
        insights = self._business_insights(profile, canonical_path, available, filters, time_field, coverage, data)
        if "insights_top" in data:
            data["insights_top"] = {"status": "ok" if insights else "empty", "widget_id": "insights_top", "insights": [item.model_dump() for item in insights]}
        count = self.engine.run_query(canonical_path, QuerySpec(measures=[MeasureSpec(alias="rows", aggregation="count")], filters=filters)).rows[0]["rows"]
        comparison_options = self._comparison_options(current_range, coverage)
        spec = DashboardSpec(profile_id=profile.id, sections=sections, filters=derive_filters(self.engine, canonical_path, fields, available, profile.bi.extra_filters if profile.bi else ()), unavailable_metrics=unavailable, comparison_options=comparison_options, terminology=profile.data.terminology.get("es", {}), key_chart_ids=key_charts)
        return spec, data, int(count), warnings

    @staticmethod
    def _date_filters(filters,time_field):
        # Date-only bounds include the whole canonical day; explicit timestamps remain exact.
        result=[]
        for item in filters:
            if item.field == time_field and item.op in {"between","gte","lte"}:
                values=[]
                for index,value in enumerate(item.values):
                    if isinstance(value,date) and not isinstance(value,datetime) or isinstance(value,str) and len(value)==10:
                        try:
                            day=value if isinstance(value,date) else date.fromisoformat(value)
                        except ValueError:
                            values.append(value)
                            continue
                        upper=item.op=="lte" or item.op=="between" and index==1
                        value=datetime.combine(day,time.max if upper else time.min)
                    values.append(value)
                item=item.model_copy(update={"values":values})
            result.append(item)
        return result

    @classmethod
    def _previous_filters(cls,filters,time_field,previous_range):
        return [*[item for item in filters if item.field!=time_field],FilterClause(field=time_field,op="between",values=[previous_range.from_date,previous_range.to_date])]

    def _with_comparison(self,result,metric_id,path,available,filters,time_field,comparison,current_range,coverage,counts):
        metric=self.metrics.get(metric_id)
        previous_range=self.comparisons.previous_range(comparison.mode,current_range) if current_range else None
        base=dict(mode=comparison.mode,current_range=current_range,previous_range=previous_range,polarity=metric.polarity)
        reason=None
        if not metric.comparable: reason="comparison.metric_not_comparable"
        elif current_range is None or coverage is None: reason="comparison.no_date" if coverage is None or coverage.minimum is None or coverage.maximum is None else "comparison.unsupported_time_filter"
        elif not self.comparisons.equivalent(comparison.mode,current_range,previous_range): reason="comparison.unequal_periods"
        elif self.comparisons.coverage_ratio(previous_range,coverage)<0.30: reason="comparison.insufficient_data"
        elif self.comparisons.coverage_ratio(current_range,coverage)<0.30: reason="comparison.current_insufficient_data"
        elif counts and counts[0]==0: reason="comparison.current_no_observations"
        elif counts and counts[1]==0: reason="comparison.previous_no_observations"
        elif result.status!="ok": reason="comparison.current_unavailable"
        if reason:
            resolved=ComparisonResult(**base,status="not_applicable" if reason in {"comparison.metric_not_comparable","comparison.no_date","comparison.unsupported_time_filter","comparison.unequal_periods"} else "insufficient_data",reason_key=reason)
        else:
            previous=self.metric_engine.evaluate(path,metric_id,available,self._previous_filters(filters,time_field,previous_range))
            currency_mismatch=metric.currency_sensitive and result.format.type=="currency" and result.format.currency!=previous.format.currency
            if previous.status!="ok" or currency_mismatch:
                resolved=ComparisonResult(**base,status="insufficient_data",reason_key="comparison.currency_mismatch" if currency_mismatch or any(w.code=="MIXED_CURRENCY" for w in previous.warnings) else "comparison.previous_unavailable")
            else:
                resolved=self.comparisons.resolve(comparison.mode,current_range,coverage,result.value,previous.value,percentage_metric=metric.output.type=="percent").model_copy(update={"polarity":metric.polarity})
        return result.model_copy(update={"comparison":resolved})

    def _widget(self, widget: WidgetTemplate, path: Path, available: set[str], filters: list[FilterClause], time_field: str, grain: str, quality):
        if widget.type == "kpi":
            return self.metric_engine.evaluate(path, widget.metric_id or "", available, filters)
        if widget.type == "quality":
            summary = quality
            return QualityResult(widget_id=widget.id, total_issues=summary.total_issues if summary else 0, error_count=summary.error_count if summary else 0, warning_count=summary.warning_count if summary else 0, info_count=summary.info_count if summary else 0)
        if widget.type == "insights":
            return {"status": "empty", "widget_id": widget.id, "insights": []}
        metric_status = self.metric_engine.evaluate(path, widget.metric_id or "revenue", available, filters)
        if metric_status.status == "unavailable":
            return ChartResult(status="unavailable", widget_id=widget.id, chart="timeseries" if widget.type == "timeseries" else "breakdown", x_type="time" if widget.type == "timeseries" else "category", meta={"reason_key": metric_status.warnings[0].message_key if metric_status.warnings else None})
        dimension = time_field if widget.type == "timeseries" else widget.dimension or ""
        metric = widget.metric_id or "revenue"
        key, groups = self.metric_engine.grouped(path, metric, available, filters, GroupBy(field=dimension, grain=grain if widget.type == "timeseries" else None))
        values = [[str(label), value] for label, value in groups if (widget.type != "timeseries" or label is not None and str(label) not in {"NaT", "<NA>", "nan"}) and value is not None]
        if widget.type != "timeseries":
            values.sort(key=lambda point: (-point[1], point[0]))
        total = metric_status.value
        points = [point if widget.type == "timeseries" else [*point, point[1] / total if self.metrics.get(metric).additive and total else None] for point in values]
        if widget.top_n and len(points) > widget.top_n:
            selected = points[:widget.top_n]
            if widget.type != "timeseries":
                selected_values = [label for label, _ in groups if str(label) in {point[0] for point in selected}]
                other = self.metric_engine.evaluate(path, metric, available, [*filters, FilterClause(field=dimension, op="not_in", values=selected_values)])
                if other.value is not None:
                    selected.append(["Otros", other.value, other.value / total if self.metrics.get(metric).additive and total else None])
            points = selected
        return ChartResult(status="ok" if points else "empty", widget_id=widget.id, chart="timeseries" if widget.type == "timeseries" else "ranking" if widget.type == "ranking" else "breakdown", x_type="time" if widget.type == "timeseries" else "category", grain=grain if widget.type == "timeseries" else None, series=[ChartSeries(key=metric, label_key=f"metric.{metric}", points=points)], meta={"has_others_bucket": any(point[0] == "Otros" for point in points), "dimension": dimension})

    @staticmethod
    def _period_bounds(value, grain):
        from calendar import monthrange
        from datetime import date, datetime, timetime, timedelta
        if grain == "year":
            year = int(value)
            return date(year, 1, 1), datetime.combine(date(year, 12, 31), datetime.max.time())
        if grain == "quarter":
            year, quarter = value.split("Q")
            month = (int(quarter) - 1) * 3 + 1
            return date(int(year), month, 1), datetime.combine(date(int(year), month + 2, monthrange(int(year), month + 2)[1]), datetime.max.time())
        start = date.fromisoformat(value + "-01" if grain == "month" else value)
        end = date(start.year, start.month, monthrange(start.year, start.month)[1]) if grain == "month" else start + timedelta(days=6) if grain == "week" else start
        return start, datetime.combine(end, datetime.max.time())

    @staticmethod
    def _current_range(filters,time_field,coverage):
        if not coverage or not coverage.minimum or not coverage.maximum:
            return None
        clauses=DashboardBuilder._date_filters([item for item in filters if item.field==time_field],time_field)
        if any(item.op not in {"between","gte","lte"} for item in clauses): return None
        starts=[];ends=[]
        for item in clauses:
            # Intraday filters cannot be represented faithfully by a DateRange.
            for index,value in enumerate(item.values):
                try:
                    parsed=datetime.fromisoformat(str(value))
                except ValueError:
                    return None
                upper=item.op=="lte" or item.op=="between" and index==1
                if parsed.tzinfo or parsed.time()!=(time.max if upper else time.min): return None
            if item.op in {"between","gte"}: starts.append(date.fromisoformat(str(item.values[0])[:10]))
            if item.op in {"between","lte"}: ends.append(date.fromisoformat(str(item.values[-1])[:10]))
        return DateRange(from_date=max(starts) if starts else coverage.minimum,to_date=min(ends) if ends else coverage.maximum)

    def _comparison_options(self, current, coverage):
        modes = ["none", "previous_period", "previous_week", "previous_month", "previous_quarter", "previous_year"]
        options = []
        for mode in modes:
            previous = self.comparisons.previous_range(mode, current) if current else None
            ratio = self.comparisons.coverage_ratio(previous, coverage) if previous and coverage else 0
            options.append(ComparisonOption(mode=mode, available=mode == "none" or ratio >= 0.30 and self.comparisons.equivalent(mode,current,previous), reason_key=None if mode == "none" or ratio >= 0.30 and self.comparisons.equivalent(mode,current,previous) else "comparison.insufficient_data"))
        return options

    def _business_insights(self, profile, path, available, filters, time_field, coverage, data):
        results = [value for value in data.values() if isinstance(value, MetricResult)]
        dimensions = sorted({value.meta.get("dimension") for value in data.values()
            if isinstance(value, ChartResult) and value.x_type == "category" and value.meta.get("dimension") in available})
        grouped = {}
        # Rankings and contributions reuse the registry AST; F1 supplies comparable windows.
        for result in results:
            if result.status != "ok" or result.value is None: continue
            for dimension in dimensions:
                if result.metric_id != "revenue" and not self.metrics.get(result.metric_id).additive: continue
                _, values = self.metric_engine.grouped(path, result.metric_id, available, filters, GroupBy(field=dimension))
                current = dict(values)
                previous = None
                comparisons = {}
                c = result.comparison
                if c and c.status in {"ok", "previous_zero"} and c.previous_range and coverage:
                    _, values = self.metric_engine.grouped(path, result.metric_id, available,
                        self._previous_filters(filters, time_field, c.previous_range), GroupBy(field=dimension))
                    previous = dict(values)
                    for segment in current.keys() & previous.keys():
                        comparisons[segment] = self.comparisons.resolve(c.mode, c.current_range, coverage,
                            current[segment], previous[segment], percentage_metric=result.format.type == "percent")
                grouped[(result.metric_id, dimension)] = (current, previous, comparisons)
        return business_insights(profile, self.metrics, results, grouped,
                                 [clause.model_dump(mode="json") for clause in filters])
