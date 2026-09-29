"""Resolve metric availability from canonical fields."""

from bi.metrics.models import MetricAvailability
from bi.metrics.registry import MetricRegistry


def resolve_availability(registry: MetricRegistry, available_fields: set[str]) -> dict[str, MetricAvailability]:
    resolved: dict[str, MetricAvailability] = {}
    for metric in registry.all():
        missing = ["|".join(sorted(options)) for options in registry.requirement_options(metric.id) if not options.intersection(available_fields)]
        resolved[metric.id] = MetricAvailability(available=not missing, missing_fields=missing)
    return resolved

