"""Explicit canonical parsing. Pandas types never escape this module."""

from pathlib import Path

import pandas as pd

from analytics_core.canonical.derived import DerivedFieldRule
from analytics_core.canonical.fields import FieldSpec
from analytics_core.cleaning.models import CanonicalBuildResult, Transformation
from analytics_core.ingestion.models import SourceSettings
from analytics_core.mapping.matcher import normalize_name
from analytics_core.mapping.models import ColumnDisposition, ColumnMapping
from analytics_core.validation.models import ParseReport


def _number(series: pd.Series, settings: SourceSettings) -> pd.Series:
    decimal = settings.decimal or "."
    thousands = settings.thousands
    text = series.astype("string").str.strip().str.replace(r"[$€£\s]", "", regex=True)
    if thousands:
        text = text.str.replace(thousands, "", regex=False)
    if decimal != ".":
        text = text.str.replace(decimal, ".", regex=False)
    return pd.to_numeric(text, errors="coerce")


def _parse(series: pd.Series, field: FieldSpec, settings: SourceSettings) -> pd.Series:
    if field.dtype in {"decimal", "integer"}:
        parsed = _number(series, settings)
        return parsed.astype("Int64") if field.dtype == "integer" else parsed.astype("Float64")
    if field.dtype in {"date", "datetime"}:
        parsed = pd.to_datetime(series.astype("string").str.strip(), errors="coerce", dayfirst=bool(settings.date_dayfirst))
        return parsed.dt.normalize() if field.dtype == "date" else parsed
    if field.dtype == "boolean":
        values = series.astype("string").str.strip().str.lower()
        return values.map({"true": True, "false": False, "1": True, "0": False, "sí": True, "si": True, "no": False}).astype("boolean")
    return series.astype("string")


def build_frame(
    raw_path: Path,
    mappings: list[ColumnMapping],
    fields: list[FieldSpec],
    column_names: dict[str, str],
    settings: SourceSettings,
    derived_rules: list[DerivedFieldRule],
) -> tuple[pd.DataFrame, list[ParseReport], list[Transformation]]:
    raw = pd.read_parquet(raw_path)
    canonical = pd.DataFrame({"_row_id": range(1, len(raw) + 1)})
    catalog = {field.id: field for field in fields}
    reports: list[ParseReport] = []
    transformations: list[Transformation] = []
    seq = 0
    used_names: set[str] = set()
    for mapping in mappings:
        if mapping.disposition == ColumnDisposition.ignored:
            continue
        source = raw[mapping.column_key].astype("string")
        if mapping.disposition == ColumnDisposition.canonical:
            target = mapping.target_field or ""
            field = catalog[target]
        else:
            base = normalize_name(column_names.get(mapping.column_key, mapping.column_key)) or mapping.column_key
            target = f"custom__{base}"
            if target in used_names:
                target = f"{target}__{mapping.column_key}"
            field = FieldSpec(id=target, label_key=target, kind="measure" if mapping.disposition == ColumnDisposition.custom_measure else "dimension", dtype="decimal" if mapping.disposition == ColumnDisposition.custom_measure else "string", scope="custom")
        used_names.add(target)
        parsed = _parse(source, field, settings)
        blank = source.fillna("").str.strip().eq("")
        invalid = ~blank & parsed.isna()
        canonical[target] = parsed
        canonical[f"_valid__{target}"] = ~invalid
        report = ParseReport(total_rows=len(raw), parsed_rows=int((~blank & ~invalid).sum()), invalid_rows=int(invalid.sum()), invalid_ratio=round(float(invalid.mean()), 6) if len(raw) else 0.0, field_id=target, source_column_key=mapping.column_key, parse_type=field.dtype, sample_row_ids=canonical.loc[invalid, "_row_id"].head(10).astype(int).tolist())
        reports.append(report)
        if field.dtype in {"decimal", "integer", "date", "datetime", "boolean"}:
            seq += 1
            transformations.append(Transformation(id=f"t{seq:03d}", seq=seq, action_id="parse_numbers" if field.dtype in {"decimal", "integer"} else "parse_dates", kind="parse", columns=[target], rows_before=len(raw), rows_after=len(raw), rows_affected=report.parsed_rows, summary=f"Se convirtió {target} al tipo {field.dtype}.", automatic=True))
    for rule in derived_rules:
        if rule.target_field not in canonical and all(field in canonical for field in rule.source_fields):
            left, right = rule.source_fields
            canonical[rule.target_field] = canonical[left] * canonical[right]
            canonical[f"_valid__{rule.target_field}"] = canonical[f"_valid__{left}"] & canonical[f"_valid__{right}"]
            seq += 1
            transformations.append(Transformation(id=f"t{seq:03d}", seq=seq, action_id=rule.id, kind="derive", columns=[rule.target_field], rows_before=len(raw), rows_after=len(raw), rows_affected=int(canonical[rule.target_field].notna().sum()), summary=f"Se derivó {rule.target_field} desde {' y '.join(rule.source_fields)}.", automatic=True))
    return canonical, reports, transformations


def persist_result(frame: pd.DataFrame, path: Path, reports: list[ParseReport], transformations: list[Transformation]) -> CanonicalBuildResult:
    path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_parquet(path, index=False)
    visible = [column for column in frame.columns if not column.startswith("_valid__") and column != "_row_id"]
    return CanonicalBuildResult(row_count=len(frame), column_count=len(visible), columns=visible, parse_reports=reports, transformations=transformations)
