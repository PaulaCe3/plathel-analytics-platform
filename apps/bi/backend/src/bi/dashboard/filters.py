"""Dynamic filter derivation and bounded option lookup."""

from pathlib import Path

from analytics_core.canonical.fields import FieldSpec
from analytics_core.engine.base import DataEngine
from analytics_core.engine.query import FilterClause, GroupBy, MeasureSpec, OrderBy, QuerySpec
from bi.dashboard.widgets import FilterDefinition, FilterOption


def option_values(engine: DataEngine, path: Path, field: str, query: str | None = None, limit: int = 50) -> list[FilterOption]:
    filters = [FilterClause(field=field, op="contains", values=[query])] if query else []
    result = engine.run_query(path, QuerySpec(measures=[MeasureSpec(alias="count", aggregation="count")], group_by=[GroupBy(field=field)], filters=filters, order_by=[OrderBy(field="count", direction="desc")], limit=min(max(limit, 1), 100)))
    return [FilterOption(value=str(row[field]), count=int(row["count"])) for row in result.rows if row.get(field) not in (None, "")]


def derive_filters(engine: DataEngine, path: Path, fields: list[FieldSpec], available: set[str], extra_order: tuple[str, ...] = ()) -> list[FilterDefinition]:
    catalog = {field.id: field for field in fields if field.id in available and field.kind in {"time", "dimension", "identifier"}}
    order = [field for field in extra_order if field in catalog] + [field for field in catalog if field not in extra_order]
    definitions: list[FilterDefinition] = []
    for field_id in order:
        field = catalog[field_id]
        if field.kind == "time":
            coverage = engine.date_coverage(path, field_id)
            definitions.append(FilterDefinition(id=field_id, field=field_id, type="date_range", label_key=field.label_key, minimum=coverage.minimum.isoformat() if coverage.minimum else None, maximum=coverage.maximum.isoformat() if coverage.maximum else None, presets=["last_30_days", "last_90_days", "month", "quarter", "year"]))
            continue
        probe = option_values(engine, path, field_id, limit=100)
        high = len(probe) >= 100
        definitions.append(FilterDefinition(id=field_id, field=field_id, type="search" if high else "multi_select", label_key=field.label_key, options=[] if high else probe))
    return definitions
