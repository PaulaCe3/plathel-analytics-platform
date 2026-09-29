from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq

from analytics_core.canonical.derived import UNIVERSAL_DERIVED_RULES
from analytics_core.canonical.fields import UNIVERSAL_FIELDS
from analytics_core.cleaning.models import CleaningActionSpec
from analytics_core.engine.pandas_impl import PandasDataEngine
from analytics_core.ingestion.models import SourceSettings
from analytics_core.mapping.models import ColumnMapping


def raw_file(path: Path) -> Path:
    pq.write_table(pa.table({
        "c01": ["2026-01-01", "fecha mala", "2026-01-01"],
        "c02": ["  Producto A ", "Producto B", "  Producto A "],
        "c03": ["10,5", "texto", "10,5"],
        "c04": ["2", "-1", "2"],
        "c05": ["ARS", "USD", "ARS"],
        "c06": ["", "", ""],
        "c07": ["ignorar", "ignorar", "ignorar"],
    }), path)
    return path


def mappings() -> list[ColumnMapping]:
    return [
        ColumnMapping(column_key="c01", target_field="date", disposition="canonical"),
        ColumnMapping(column_key="c02", target_field="concept", disposition="canonical"),
        ColumnMapping(column_key="c03", target_field="unit_price", disposition="canonical"),
        ColumnMapping(column_key="c04", target_field="quantity", disposition="canonical"),
        ColumnMapping(column_key="c05", target_field="currency", disposition="canonical"),
        ColumnMapping(column_key="c06", disposition="custom_dimension"),
        ColumnMapping(column_key="c07", disposition="ignored"),
    ]


def build(tmp_path: Path, actions=None):
    engine = PandasDataEngine()
    raw = raw_file(tmp_path / "raw.parquet")
    canonical = tmp_path / "canonical.parquet"
    result = engine.build_canonical(raw, canonical, mappings(), list(UNIVERSAL_FIELDS), {f"c{i:02d}": name for i, name in enumerate(["fecha", "producto", "precio", "cantidad", "moneda", "campo vacio", "secreto"], 1)}, SourceSettings(decimal=","), list(UNIVERSAL_DERIVED_RULES), actions or [])
    return engine, raw, canonical, result


def test_canonical_mapping_types_validity_custom_ignored_and_raw_integrity(tmp_path: Path) -> None:
    engine, raw, canonical, result = build(tmp_path)
    table = pq.read_table(canonical).to_pydict()
    assert {"date", "concept", "unit_price", "quantity", "currency", "custom__campo_vacio", "amount"} <= set(table)
    assert "c07" not in table and "custom__secreto" not in table
    assert table["unit_price"] == [10.5, None, 10.5]
    assert table["_valid__unit_price"] == [True, False, True]
    assert table["_valid__date"] == [True, False, True]
    assert len(table["_row_id"]) == 3
    assert pq.read_table(raw).column_names == [f"c{i:02d}" for i in range(1, 8)]
    assert any(item.action_id == "amount_from_unit_price_quantity" for item in result.transformations)


def test_quality_plan_actions_audit_determinism_and_reset(tmp_path: Path) -> None:
    engine, raw, canonical, base = build(tmp_path)
    quality = engine.inspect_quality(canonical, base.parse_reports, [])
    codes = {issue.code for issue in quality.issues}
    assert {"MISSING_VALUES", "EMPTY_COLUMN", "DUPLICATE_ROWS", "INVALID_DATES", "INVALID_NUMBERS", "NEGATIVE_QUANTITIES", "LEADING_TRAILING_SPACES", "MIXED_CURRENCY"} <= codes
    plan = engine.create_cleaning_plan(canonical, base.parse_reports, quality)
    destructive = [action for action in plan.actions if action.destructive]
    assert destructive and not any(action.selected for action in destructive)
    actions = [CleaningActionSpec(id="trim_whitespace", selected=True, description="trim"), CleaningActionSpec(id="drop_empty_columns", destructive=True, selected=True, description="empty"), CleaningActionSpec(id="drop_exact_duplicates", destructive=True, selected=True, description="duplicates")]
    first = engine.build_canonical(raw, canonical, mappings(), list(UNIVERSAL_FIELDS), {"c01": "fecha", "c02": "producto", "c03": "precio", "c04": "cantidad", "c05": "moneda", "c06": "campo vacio", "c07": "secreto"}, SourceSettings(decimal=","), list(UNIVERSAL_DERIVED_RULES), actions)
    first_table = pq.read_table(canonical).to_pydict()
    second = engine.build_canonical(raw, canonical, mappings(), list(UNIVERSAL_FIELDS), {"c01": "fecha", "c02": "producto", "c03": "precio", "c04": "cantidad", "c05": "moneda", "c06": "campo vacio", "c07": "secreto"}, SourceSettings(decimal=","), list(UNIVERSAL_DERIVED_RULES), actions)
    assert first_table == pq.read_table(canonical).to_pydict()
    assert [(item.action_id, item.rows_affected, item.rows_before, item.rows_after) for item in first.transformations] == [(item.action_id, item.rows_affected, item.rows_before, item.rows_after) for item in second.transformations]
    assert all(len(item.examples) <= 3 for item in second.transformations)
    assert second.row_count == 2
    reset = engine.build_canonical(raw, canonical, mappings(), list(UNIVERSAL_FIELDS), {"c01": "fecha", "c02": "producto", "c03": "precio", "c04": "cantidad", "c05": "moneda", "c06": "campo vacio", "c07": "secreto"}, SourceSettings(decimal=","), list(UNIVERSAL_DERIVED_RULES), [])
    assert reset.row_count == 3


def test_drop_rows_is_explicit_and_logged(tmp_path: Path) -> None:
    engine, raw, canonical, _ = build(tmp_path)
    action = CleaningActionSpec(id="drop_rows", params={"row_ids": [2]}, destructive=True, selected=True, description="row")
    result = engine.build_canonical(raw, canonical, mappings(), list(UNIVERSAL_FIELDS), {f"c{i:02d}": f"col{i}" for i in range(1, 8)}, SourceSettings(decimal=","), list(UNIVERSAL_DERIVED_RULES), [action])
    assert result.row_count == 2
    logged = result.transformations[-1]
    assert logged.action_id == "drop_rows" and logged.rows_affected == 1 and not logged.automatic
