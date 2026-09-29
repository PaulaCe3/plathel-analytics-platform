"""In-process registry for declarative metric definitions."""

from bi.metrics.expr import Expr, field_options, required_fields
from bi.metrics.models import MetricDefinition


class MetricRegistry:
    def __init__(self) -> None:
        self._metrics: dict[str, MetricDefinition] = {}

    def register(self, metric: MetricDefinition) -> None:
        if metric.id in self._metrics:
            raise ValueError(f"Metric already registered: {metric.id}")
        self._metrics[metric.id] = metric
        object.__setattr__(metric, "_expr_resolver", self._expr)

    def get(self, metric_id: str) -> MetricDefinition:
        try:
            return self._metrics[metric_id]
        except KeyError as exc:
            raise KeyError(f"Unknown metric: {metric_id}") from exc

    def all(self) -> tuple[MetricDefinition, ...]:
        return tuple(self._metrics.values())

    def _expr(self, metric_id: str) -> Expr:
        return self.get(metric_id).expr

    def requirements(self, metric_id: str) -> set[str]:
        return required_fields(self.get(metric_id).expr, self._expr)

    def requirement_options(self, metric_id: str) -> tuple[frozenset[str], ...]:
        return field_options(self.get(metric_id).expr, self._expr)
