"""Validated monthly forecast facade; model selection lives in the forecast engine."""
from datetime import date
from math import isfinite

from forecast.engine import PREDICTION_COVERAGE, empirical_range, select_forecast
from forecast.models import ForecastPoint, ForecastResult

MIN_HISTORY = 24


def month_number(period: str) -> int:
    year, month = map(int, period.split("-"))
    if not 1 <= month <= 12:
        raise ValueError("invalid month")
    return year * 12 + month - 1


def period_name(number: int) -> str:
    return f"{number // 12:04d}-{number % 12 + 1:02d}"


def estimate(points: list[ForecastPoint], field: str, label: str, horizon: int, excluded_rows: int = 0, today: date | None = None) -> ForecastResult:
    result = ForecastResult(status="unavailable", explanation="Necesitamos al menos 24 meses completos consecutivos, con valores válidos y sin meses faltantes.", field=field, label=label, horizon=horizon, excluded_rows=excluded_rows)
    current = today or date.today()
    cutoff = current.year * 12 + current.month - 1
    try:
        history = sorted((point for point in points if month_number(point.period) < cutoff), key=lambda point: point.period)
    except (TypeError, ValueError):
        result.explanation = "Hay fechas o valores no válidos. Revisá tus datos antes de crear una predicción."
        return result
    result.history = history
    result.observations = len(history)
    result.limitations = ["Se suman los valores por mes; no se rellenan meses sin datos.", "Se omiten el mes actual y las fechas futuras porque no representan meses completos.", "Los modelos usan solo el historial anterior a cada mes evaluado y no incorporan causas externas.", f"El rango estimado refleja errores históricos con cobertura central del {round(PREDICTION_COVERAGE * 100)} %; no garantiza el resultado futuro.", "La continuidad de meses no garantiza que el archivo incluya todas las operaciones de cada mes."]
    if excluded_rows:
        result.explanation = "Hay fechas o valores no válidos. Revisá tus datos antes de crear una predicción."
        return result
    if len(history) < MIN_HISTORY or any(not isfinite(point.value) for point in history):
        return result
    months = [month_number(point.period) for point in history]
    if len(set(months)) != len(months) or any(right - left != 1 for left, right in zip(months, months[1:])):
        return result
    selected = select_forecast([point.value for point in history], horizon)
    if selected is None:
        return result
    prediction = []
    for step, value in enumerate(selected.values, start=1):
        bounds = empirical_range(value, selected.errors_by_step[step - 1])
        prediction.append(ForecastPoint(period=period_name(months[-1] + step), value=value, lower=bounds[0] if bounds else None, upper=bounds[1] if bounds else None))
    result.status = "ok"
    result.model = selected.candidate.name
    result.evaluation_value = selected.mae
    result.evaluation_periods = selected.evaluations
    result.candidate_evaluations = selected.candidates
    result.prediction = prediction
    result.explanation = f"Estimación del total mensual de {label.lower()} para los {horizon} meses posteriores al último mes observado. Se compararon modelos mediante pruebas históricas sin usar datos futuros."
    first = prediction[0]
    result.interpretation = (f"Según el comportamiento histórico, {label.lower()} para {first.period} se estima en {first.value:g}, con un rango estimado de {first.lower:g} a {first.upper:g}." if first.lower is not None and first.upper is not None else f"Según el comportamiento histórico, {label.lower()} para {first.period} se estima en {first.value:g}.")
    return result
