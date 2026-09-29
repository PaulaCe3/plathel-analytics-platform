"""Universal metric catalog."""

from bi.metrics.expr import AnyOf, Count, CountDistinct, Field, MetricRef, Ratio, Sum
from bi.metrics.models import MetricDefinition, OutputSpec
from bi.metrics.registry import MetricRegistry


def build_universal_registry() -> MetricRegistry:
    registry = MetricRegistry()
    definitions = (
        MetricDefinition(id="revenue", label_key="metric.revenue", description_key="metric.revenue.description", group="sales", expr=Sum(Field("amount")), output=OutputSpec(type="currency", decimals=2), currency_sensitive=True),
        MetricDefinition(id="transactions", label_key="metric.transactions", description_key="metric.transactions.description", group="volume", expr=CountDistinct(Field("transaction_id"), fallback=Count()), output=OutputSpec(type="integer")),
        MetricDefinition(id="customers", label_key="metric.customers", description_key="metric.customers.description", group="customers", expr=CountDistinct(AnyOf("customer_id", "customer_name")), output=OutputSpec(type="integer"), additive=False),
        MetricDefinition(id="avg_transaction_value", label_key="metric.avg_transaction_value", description_key="metric.avg_transaction_value.description", group="sales", expr=Ratio(MetricRef("revenue"), MetricRef("transactions")), output=OutputSpec(type="currency", decimals=2), additive=False, currency_sensitive=True),
        MetricDefinition(id="quantity", label_key="metric.quantity", description_key="metric.quantity.description", group="volume", expr=Sum(Field("quantity")), output=OutputSpec(type="number", decimals=2)),
        MetricDefinition(id="avg_unit_price", label_key="metric.avg_unit_price", description_key="metric.avg_unit_price.description", group="sales", expr=Ratio(MetricRef("revenue"), MetricRef("quantity")), output=OutputSpec(type="currency", decimals=2), additive=False, currency_sensitive=True),
    )
    for definition in definitions:
        registry.register(definition)
    return registry


UNIVERSAL_METRICS = build_universal_registry()

