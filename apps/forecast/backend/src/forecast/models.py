"""Forecast API contracts: results, availability and evaluation are explicit."""
from typing import Literal
from pydantic import BaseModel, Field


class ForecastChoice(BaseModel):
    field: str
    label: str
    available: bool
    explanation: str


class ForecastOptions(BaseModel):
    dataset_id: str
    status: Literal["ok", "unavailable"]
    explanation: str
    choices: list[ForecastChoice] = Field(default_factory=list)


class ForecastRequest(BaseModel):
    field: str = Field(min_length=1, max_length=100)
    horizon: int = Field(default=3, ge=1, le=6)


class ForecastPoint(BaseModel):
    period: str
    value: float


class ForecastResult(BaseModel):
    status: Literal["ok", "unavailable"]
    explanation: str
    field: str
    label: str = ""
    horizon: int
    history: list[ForecastPoint] = Field(default_factory=list)
    prediction: list[ForecastPoint] = Field(default_factory=list)
    observations: int = 0
    excluded_rows: int = 0
    model: str = "Referencia estacional anual"
    evaluation_metric: str = "Error absoluto medio"
    evaluation_value: float | None = None
    evaluation_periods: int = 6
    interpretation: str = ""
    limitations: list[str] = Field(default_factory=list)
