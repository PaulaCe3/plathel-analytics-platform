"""Hospitality metrics require mapped nights; no date derivation or occupancy."""
from bi.metrics.expr import Field, Mean, MetricRef, Ratio, Sum
from bi.metrics.models import MetricDefinition, OutputSpec

DEFINITIONS = (
    MetricDefinition(id="total_nights", label_key="metric.total_nights", description_key="metric.total_nights.description", group="volume", expr=Sum(Field("nights")), output=OutputSpec(type="number", decimals=2), industries=["hospitality"], polarity="neutral"),
    MetricDefinition(id="adr", label_key="metric.adr", description_key="metric.adr.description", group="sales", expr=Ratio(MetricRef("revenue"), MetricRef("total_nights")), output=OutputSpec(type="currency", decimals=2), industries=["hospitality"], additive=False, currency_sensitive=True),
    MetricDefinition(id="average_stay", label_key="metric.average_stay", description_key="metric.average_stay.description", group="volume", expr=Mean(Field("nights")), output=OutputSpec(type="number", decimals=2), industries=["hospitality"], additive=False, polarity="neutral"),
)
SEMANTICS = {}
