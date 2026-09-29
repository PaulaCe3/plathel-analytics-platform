"""Full-table quality inspection without modification."""

from pathlib import Path

import pandas as pd

from analytics_core.cleaning.models import CleaningActionSpec, CleaningPlan
from analytics_core.quality.models import DataQualityReport, quality_report
from analytics_core.validation.models import Issue, ParseReport, ProfileCheck


def inspect(path: Path, reports: list[ParseReport], profile_checks: list[ProfileCheck]) -> DataQualityReport:
    frame = pd.read_parquet(path)
    issues: list[Issue] = []
    visible = [name for name in frame.columns if name != "_row_id" and not name.startswith("_valid__")]
    for column in visible:
        missing = _missing_mask(frame[column])
        if missing.any():
            issues.append(_issue("MISSING_VALUES", "warning", "Se encontraron valores faltantes.", column, int(missing.sum()), len(frame), "completeness"))
        if bool(missing.all()):
            issues.append(_issue("EMPTY_COLUMN", "warning", "La columna está completamente vacía.", column, len(frame), len(frame), "structure", "drop_empty_columns"))
        if column in {"amount", "quantity"}:
            negative = frame[column].notna() & (frame[column] < 0)
            if negative.any():
                code = "NEGATIVE_AMOUNTS" if column == "amount" else "NEGATIVE_QUANTITIES"
                issues.append(_issue(code, "warning", "Se encontraron valores negativos; pueden representar ajustes o devoluciones.", column, int(negative.sum()), len(frame), "business"))
        if pd.api.types.is_string_dtype(frame[column].dtype) or frame[column].dtype == object:
            text = frame[column].astype("string")
            spaces = text.notna() & (text != text.str.strip())
            if spaces.any():
                issues.append(_issue("LEADING_TRAILING_SPACES", "info", "Hay valores con espacios al inicio o al final.", column, int(spaces.sum()), len(frame), "format", "trim_whitespace"))
    comparable = visible
    duplicates = frame.duplicated(subset=comparable, keep=False) if comparable else pd.Series(False, index=frame.index)
    if duplicates.any():
        issues.append(_issue("DUPLICATE_ROWS", "warning", "Se encontraron filas exactamente duplicadas; no fueron eliminadas.", None, int(duplicates.sum()), len(frame), "duplicates", "drop_exact_duplicates"))
    if "transaction_id" in frame:
        duplicate_ids = frame["transaction_id"].notna() & frame["transaction_id"].duplicated(keep=False)
        if duplicate_ids.any():
            issues.append(_issue("DUPLICATE_IDS", "info", "Un identificador aparece en varias filas; puede tratarse de líneas de una misma transacción.", "transaction_id", int(duplicate_ids.sum()), len(frame), "duplicates"))
    for report in reports:
        if report.invalid_rows:
            code = "INVALID_DATES" if report.parse_type in {"date", "datetime"} else "INVALID_NUMBERS" if report.parse_type in {"decimal", "integer"} else "TYPE_MISMATCH"
            issues.append(Issue(id=f"{code.lower()}:{report.field_id}", code=code, scope="field", severity="warning", message="Algunos valores no pudieron convertirse; las filas se conservaron.", field_id=report.field_id, column_key=report.source_column_key, count=report.invalid_rows, ratio=report.invalid_ratio, sample_row_ids=report.sample_row_ids, category="validity"))
    if "currency" in frame and frame["currency"].dropna().astype(str).str.strip().replace("", pd.NA).nunique() > 1:
        issues.append(_issue("MIXED_CURRENCY", "warning", "Se detectaron varias monedas; no se realizó conversión.", "currency", int(frame["currency"].dropna().nunique()), len(frame), "business"))
    text_columns = [name for name in visible if pd.api.types.is_string_dtype(frame[name].dtype) or frame[name].dtype == object]
    if text_columns:
        total_mask = frame[text_columns].fillna("").astype(str).apply(lambda column: column.str.strip().str.lower().isin({"total", "totales", "subtotal"})).any(axis=1)
        if total_mask.any():
            issues.append(_issue("SUSPICIOUS_TOTAL_ROW", "warning", "Se detectaron posibles filas de totales; no fueron eliminadas.", None, int(total_mask.sum()), len(frame), "structure", "drop_rows"))
    for check in profile_checks:
        if check.left_field in frame and check.right_field in frame and check.operation == "greater_than":
            applicable = frame[check.left_field].notna() & frame[check.right_field].notna()
            failed = applicable & ~(frame[check.left_field] > frame[check.right_field])
            if failed.any():
                issues.append(Issue(id=f"profile_check:{check.id}", code="PROFILE_CHECK_FAILED", scope="profile", severity=check.severity, message=check.message, field_id=check.left_field, count=int(failed.sum()), ratio=round(float(failed.mean()), 6), sample_row_ids=frame.loc[failed, "_row_id"].head(10).astype(int).tolist(), category="profile"))
    return quality_report(issues)


def cleaning_plan(path: Path, reports: list[ParseReport], quality: DataQualityReport) -> CleaningPlan:
    frame = pd.read_parquet(path)
    visible = [name for name in frame.columns if name != "_row_id" and not name.startswith("_valid__")]
    string_columns = [name for name in visible if pd.api.types.is_string_dtype(frame[name].dtype) or frame[name].dtype == object]
    spaces = sum(int((frame[name].astype("string") != frame[name].astype("string").str.strip()).fillna(False).sum()) for name in string_columns)
    empty = sum(bool(_missing_mask(frame[name]).all()) for name in visible)
    duplicates = int(frame.duplicated(subset=visible, keep="first").sum()) if visible else 0
    parse_dates = sum(report.parsed_rows for report in reports if report.parse_type in {"date", "datetime"})
    parse_numbers = sum(report.parsed_rows for report in reports if report.parse_type in {"decimal", "integer"})
    total_rows = next((issue.count or 0 for issue in quality.issues if issue.code == "SUSPICIOUS_TOTAL_ROW"), 0)
    return CleaningPlan(actions=[
        CleaningActionSpec(id="parse_dates", selected=True, estimated_values_affected=parse_dates, description=f"Se interpretaron {parse_dates} valores de fecha."),
        CleaningActionSpec(id="parse_numbers", selected=True, estimated_values_affected=parse_numbers, description=f"Se interpretaron {parse_numbers} valores numéricos."),
        CleaningActionSpec(id="trim_whitespace", selected=spaces > 0, estimated_values_affected=spaces, description=f"Se normalizarían {spaces} valores con espacios."),
        CleaningActionSpec(id="drop_empty_columns", destructive=True, selected=False, estimated_values_affected=empty, description=f"Se eliminarían {empty} columnas vacías."),
        CleaningActionSpec(id="drop_exact_duplicates", destructive=True, selected=False, estimated_rows_affected=duplicates, description=f"Se eliminarían {duplicates} filas duplicadas exactas."),
        CleaningActionSpec(id="drop_rows", params={"row_ids": []}, destructive=True, selected=False, estimated_rows_affected=total_rows, description=f"Se podrían eliminar {total_rows} filas señaladas."),
    ])


def _issue(code: str, severity: str, message: str, field: str | None, count: int, total: int, category: str, action: str | None = None) -> Issue:
    return Issue(id=f"{code.lower()}:{field or 'dataset'}", code=code, scope="field" if field else "dataset", severity=severity, message=message, field_id=field, count=count, ratio=round(count / total, 6) if total else 0.0, suggested_action=action, category=category)


def _missing_mask(series: pd.Series) -> pd.Series:
    missing = series.isna()
    if pd.api.types.is_string_dtype(series.dtype) or series.dtype == object:
        missing = missing | series.astype("string").str.strip().eq("").fillna(False)
    return missing
