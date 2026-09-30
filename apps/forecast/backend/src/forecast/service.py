"""Reuse prepared sessions and neutral queries without importing BI."""
from analytics_core.engine.pandas_impl import PandasDataEngine
from analytics_core.engine.query import QuerySpec, MeasureSpec, GroupBy
from analytics_core.operations import heavy_operation, session_operation
from analytics_core.sessions.store import DatasetSessionStore
from forecast.model import estimate
from forecast.models import ForecastChoice, ForecastOptions, ForecastPoint, ForecastRequest, ForecastResult

LABELS = {"amount": "Importe", "quantity": "Cantidad", "cost": "Costo"}


class ForecastService:
    def __init__(self, settings, runtime=None):
        self.store = DatasetSessionStore(settings.dataset_storage_path, settings.dataset_ttl_minutes, settings.absolute_session_ttl_minutes)
        self.engine = PandasDataEngine()
        self.runtime = runtime

    def _source(self, dataset_id):
        session = self.store.get(dataset_id)
        if session.stage != "ready" or not session.cleaning_confirmed or not session.has_canonical:
            return session, [], []
        dates, measures = self.engine.temporal_columns(self.store.path(dataset_id, "canonical.parquet"))
        # Only additive universal measures and explicitly selected custom measures are eligible.
        custom = {field for field in measures if field.startswith("custom__")}
        total_cost = any(mapping.target_field == "cost" and mapping.options.get("basis") == "total" for mapping in session.mappings)
        return session, dates, [field for field in measures if (field in LABELS and (field != "cost" or total_cost)) or field in custom]

    def _label(self, session, field):
        if field in LABELS:
            return LABELS[field]
        from analytics_core.mapping.matcher import normalize_name
        key = field.removeprefix("custom__")
        return next((column.original_name for column in session.columns if key == normalize_name(column.original_name) or key == f"{normalize_name(column.original_name)}__{column.key}"), "Valor")

    def _result(self, dataset_id, session, dates, measures, request):
        label = self._label(session, request.field)
        unavailable = ForecastResult(status="unavailable", explanation="Prepará tus datos y elegí un valor disponible. Necesitamos una fecha y suficientes observaciones históricas.", field=request.field, label=label, horizon=request.horizon)
        if len(dates) != 1 or request.field not in measures:
            if len(dates) > 1:
                unavailable.explanation = "Hay varias fechas posibles. Para esta primera versión necesitamos una única fecha de referencia."
            return unavailable
        path = self.store.path(dataset_id, "canonical.parquet")
        if request.field in {"amount", "cost"} and "currency" in session.canonical_columns:
            currencies = self.engine.run_query(path, QuerySpec(measures=[MeasureSpec(alias="currencies", aggregation="count_distinct", field="currency")]))
            if currencies.rows[0]["currencies"] != 1 or any(currencies.excluded_rows.values()):
                unavailable.explanation = "Necesitamos una única moneda identificada para estimar importes sin mezclar valores."
                return unavailable
        query = QuerySpec(measures=[MeasureSpec(alias="value", aggregation="sum", field=request.field)], group_by=[GroupBy(field=dates[0], grain="month")])
        values = self.engine.run_query(path, query)
        period_field = f"{dates[0]}__month"
        points = [ForecastPoint(period=str(row[period_field]), value=float(row["value"])) for row in values.rows if row[period_field] not in {None, "NaT", "<NA>", "nan"} and row["value"] is not None]
        missing_dates = any(row[period_field] in {None, "NaT", "<NA>", "nan"} for row in values.rows)
        excluded = sum(values.excluded_rows.values()) + int(missing_dates)
        return estimate(points, request.field, label, request.horizon, excluded)

    @session_operation
    @heavy_operation
    def options(self, dataset_id):
        session, dates, measures = self._source(dataset_id)
        choices = []
        for field in measures:
            result = self._result(dataset_id, session, dates, measures, ForecastRequest(field=field))
            choices.append(ForecastChoice(field=field, label=self._label(session, field), available=result.status == "ok", explanation=result.explanation))
        ready = any(choice.available for choice in choices)
        return ForecastOptions(dataset_id=dataset_id, status="ok" if ready else "unavailable", explanation="Elegí el total mensual que querés estimar." if ready else (choices[0].explanation if choices else "Para crear una predicción necesitamos datos preparados, una fecha y al menos 24 meses completos consecutivos."), choices=choices)

    @session_operation
    @heavy_operation
    def predict(self, dataset_id, request):
        session, dates, measures = self._source(dataset_id)
        return self._result(dataset_id, session, dates, measures, request)
