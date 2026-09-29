"""Retail definitions: cost must explicitly be total; discount must be an amount."""
from bi.metrics.expr import Field, Mean, MetricRef, Ratio, Sub, Sum
from bi.metrics.models import MetricDefinition, OutputSpec

DEFINITIONS = (
    MetricDefinition(id="units_sold", label_key="metric.units_sold", description_key="metric.units_sold.description", group="volume", expr=MetricRef("quantity"), output=OutputSpec(type="number", decimals=2), industries=["retail_ecommerce"]),
    MetricDefinition(id="total_cost", label_key="metric.total_cost", description_key="metric.total_cost.description", group="profitability", expr=Sum(Field("cost")), output=OutputSpec(type="currency", decimals=2), industries=["retail_ecommerce"], currency_sensitive=True, polarity="neutral"),
    MetricDefinition(id="gross_profit", label_key="metric.gross_profit", description_key="metric.gross_profit.description", group="profitability", expr=Sub(MetricRef("revenue"), MetricRef("total_cost")), output=OutputSpec(type="currency", decimals=2), industries=["retail_ecommerce"], currency_sensitive=True),
    MetricDefinition(id="gross_margin_pct", label_key="metric.gross_margin_pct", description_key="metric.gross_margin_pct.description", group="profitability", expr=Ratio(MetricRef("gross_profit"), MetricRef("revenue")), output=OutputSpec(type="percent", decimals=2), industries=["retail_ecommerce"], additive=False, currency_sensitive=True),
    MetricDefinition(id="average_discount", label_key="metric.average_discount", description_key="metric.average_discount.description", group="sales", expr=Mean(Field("discount")), output=OutputSpec(type="currency", decimals=2), industries=["retail_ecommerce"], additive=False, currency_sensitive=True, polarity="neutral"),
)
SEMANTICS = {"cost": ("basis", "total"), "discount": ("kind", "amount")}
