"""One conservative, deterministic monthly seasonal baseline; no dataframe types."""
from datetime import date
from math import isfinite
from forecast.models import ForecastPoint, ForecastResult


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
    history = sorted((point for point in points if month_number(point.period) < cutoff), key=lambda point: point.period)
    result.history = history
    result.observations = len(history)
    result.limitations = ["Se suman los valores por mes; no se rellenan meses sin datos.", "Se omiten el mes actual y las fechas futuras porque no representan meses completos.", "Repite el valor del mismo mes del año anterior; no anticipa cambios de tendencia ni causas externas.", "No se ofrece un intervalo de confianza; la estimación no es una certeza.", "La continuidad de meses no garantiza que el archivo incluya todas las operaciones de cada mes."]
    if excluded_rows:
        result.explanation = "Hay fechas o valores no válidos. Revisá tus datos antes de crear una predicción."
        return result
    if len(history) < 24 or any(not isfinite(point.value) for point in history):
        return result
    months = [month_number(point.period) for point in history]
    if any(right - left != 1 for left, right in zip(months, months[1:])):
        return result
    # Rolling one-step evaluation on six held-out months; each estimate uses only earlier observations.
    errors = [abs(history[i].value - history[i - 12].value) for i in range(len(history) - 6, len(history))]
    result.evaluation_value = sum(errors) / len(errors)
    result.prediction = [ForecastPoint(period=period_name(months[-1] + step), value=history[-12 + step - 1].value) for step in range(1, horizon + 1)]
    result.status = "ok"
    result.explanation = f"Estimación del total mensual de {label.lower()} para los {horizon} meses posteriores al último mes observado."
    result.interpretation = "Si se repite el patrón anual, los próximos meses se aproximarían a los mismos meses del año anterior."
    return result
