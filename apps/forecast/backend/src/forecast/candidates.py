"""Small deterministic forecasting candidates with a shared interface."""
from dataclasses import dataclass
from math import isfinite
from typing import Protocol


class ForecastCandidate(Protocol):
    id: str
    name: str
    complexity: int
    minimum_history: int

    def predict(self, history: list[float], horizon: int) -> list[float] | None: ...


@dataclass(frozen=True)
class NaiveCandidate:
    id: str = "naive"
    name: str = "Último valor observado"
    complexity: int = 0
    minimum_history: int = 1

    def predict(self, history: list[float], horizon: int) -> list[float] | None:
        return [history[-1]] * horizon if history else None


@dataclass(frozen=True)
class SeasonalNaiveCandidate:
    id: str = "seasonal_naive"
    name: str = "Referencia estacional anual"
    complexity: int = 1
    minimum_history: int = 12

    def predict(self, history: list[float], horizon: int) -> list[float] | None:
        if len(history) < self.minimum_history or horizon > 12:
            return None
        return history[-12:-12 + horizon] if horizon < 12 else history[-12:]


@dataclass(frozen=True)
class LinearTrendCandidate:
    id: str = "linear_trend"
    name: str = "Tendencia lineal"
    complexity: int = 2
    minimum_history: int = 3

    def predict(self, history: list[float], horizon: int) -> list[float] | None:
        count = len(history)
        if count < self.minimum_history:
            return None
        mean_x = (count - 1) / 2
        mean_y = sum(history) / count
        denominator = sum((index - mean_x) ** 2 for index in range(count))
        if denominator == 0:
            return None
        slope = sum((index - mean_x) * (value - mean_y) for index, value in enumerate(history)) / denominator
        intercept = mean_y - slope * mean_x
        prediction = [intercept + slope * (count + step) for step in range(horizon)]
        return prediction if all(isfinite(value) for value in prediction) else None


CANDIDATES: tuple[ForecastCandidate, ...] = (NaiveCandidate(), SeasonalNaiveCandidate(), LinearTrendCandidate())
