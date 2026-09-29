"""Service metrics do not assume one service per row."""
from bi.metrics.expr import Field, MetricRef, Ratio, Sum
from bi.metrics.models import MetricDefinition, OutputSpec

DEFINITIONS = (
    MetricDefinition(id="service_hours", label_key="metric.service_hours", description_key="metric.service_hours.description", group="volume", expr=Sum(Field("duration_hours")), output=OutputSpec(type="number", decimals=2), industries=["services"], polarity="neutral"),
    MetricDefinition(id="revenue_per_hour", label_key="metric.revenue_per_hour", description_key="metric.revenue_per_hour.description", group="sales", expr=Ratio(MetricRef("revenue"), MetricRef("service_hours")), output=OutputSpec(type="currency", decimals=2), industries=["services"], additive=False, currency_sensitive=True),
)
SEMANTICS = {}
