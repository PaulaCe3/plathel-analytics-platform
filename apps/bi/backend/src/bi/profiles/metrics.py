"""Discover profile definitions without modifying engines for each industry."""
from importlib import import_module
from importlib.util import find_spec
from bi.metrics.universal import build_universal_registry


def build_profile_registry(profile, mappings=()):
    registry = build_universal_registry()
    module_name = f"bi.profiles.{profile.id}.metrics"
    if find_spec(module_name):
        module = import_module(module_name)
        for metric in module.DEFINITIONS:
            registry.register(metric)
        options = {item.target_field: item.options for item in mappings if item.target_field}
        for metric in module.DEFINITIONS:
            for field, (key, value) in module.SEMANTICS.items():
                if field in registry.requirements(metric.id) and options.get(field, {}).get(key) != value:
                    registry.blocked[metric.id] = f"metric.requires_{field}_{key}_{value}"
    if profile.bi:
        enabled = set(profile.bi.metrics)
        if not enabled <= {metric.id for metric in registry.all()}:
            raise ValueError("BIConfig references unknown metrics")
    return registry
