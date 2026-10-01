"""Rolling-origin model evaluation, deterministic selection and empirical ranges."""
from dataclasses import dataclass
from math import isfinite

from forecast.candidates import CANDIDATES, ForecastCandidate
from forecast.models import CandidateEvaluation

BACKTEST_ORIGINS = 6
MIN_EVALUATIONS = 6
MIN_INTERVAL_ERRORS = 3
PREDICTION_COVERAGE = 0.80
TIE_RELATIVE_TOLERANCE = 0.01
TIE_ABSOLUTE_TOLERANCE = 1e-9


@dataclass(frozen=True)
class SelectedForecast:
    candidate: ForecastCandidate
    values: list[float]
    mae: float
    evaluations: int
    candidates: list[CandidateEvaluation]
    errors_by_step: list[list[float]]


def _rolling_errors(candidate: ForecastCandidate, values: list[float], horizon: int) -> list[list[float]]:
    origins = [origin for origin in range(candidate.minimum_history, len(values) - horizon + 1)]
    origins = origins[-BACKTEST_ORIGINS:]
    by_step = [[] for _ in range(horizon)]
    for origin in origins:
        predicted = candidate.predict(values[:origin], horizon)
        if predicted is None or len(predicted) != horizon or not all(isfinite(value) for value in predicted):
            continue
        for step, estimate in enumerate(predicted):
            actual = values[origin + step]
            if isfinite(actual):
                by_step[step].append(actual - estimate)
    return by_step


def select_forecast(values: list[float], horizon: int) -> SelectedForecast | None:
    valid = []
    details = []
    for candidate in CANDIDATES:
        errors = _rolling_errors(candidate, values, horizon)
        flattened = [error for step in errors for error in step]
        prediction = candidate.predict(values, horizon)
        if prediction is None or len(flattened) < MIN_EVALUATIONS or not all(isfinite(value) for value in prediction):
            continue
        mae = sum(abs(error) for error in flattened) / len(flattened)
        details.append(CandidateEvaluation(model_id=candidate.id, model=candidate.name, mae=mae, evaluations=len(flattened)))
        valid.append((candidate, prediction, mae, len(flattened), errors))
    if not valid:
        return None
    best_mae = min(item[2] for item in valid)
    tolerance = max(TIE_ABSOLUTE_TOLERANCE, abs(best_mae) * TIE_RELATIVE_TOLERANCE)
    selected = min((item for item in valid if item[2] <= best_mae + tolerance), key=lambda item: item[0].complexity)
    return SelectedForecast(*selected[:4], candidates=details, errors_by_step=selected[4])


def quantile(values: list[float], probability: float) -> float:
    ordered = sorted(values)
    position = (len(ordered) - 1) * probability
    lower = int(position)
    upper = min(lower + 1, len(ordered) - 1)
    fraction = position - lower
    return ordered[lower] * (1 - fraction) + ordered[upper] * fraction


def empirical_range(prediction: float, errors: list[float]) -> tuple[float, float] | None:
    if len(errors) < MIN_INTERVAL_ERRORS or not all(isfinite(error) for error in errors):
        return None
    tail = (1 - PREDICTION_COVERAGE) / 2
    lower = min(prediction, prediction + quantile(errors, tail))
    upper = max(prediction, prediction + quantile(errors, 1 - tail))
    return (lower, upper) if isfinite(lower) and isfinite(upper) else None
