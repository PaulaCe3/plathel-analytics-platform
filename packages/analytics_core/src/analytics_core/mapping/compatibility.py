"""Lightweight compatibility inference based only on stored samples."""

from datetime import datetime

from analytics_core.canonical.fields import FieldSpec
from analytics_core.ingestion.models import ColumnMetadata


def numeric_ratio(column: ColumnMetadata) -> float:
    values = [value for value in column.sample if value not in (None, "")]
    if not values:
        return 0.0
    valid = 0
    for value in values:
        normalized = str(value).strip().replace(" ", "").replace("$", "")
        if normalized.count(",") == 1 and normalized.count(".") == 0:
            normalized = normalized.replace(",", ".")
        else:
            normalized = normalized.replace(",", "")
        try:
            float(normalized)
            valid += 1
        except ValueError:
            pass
    return valid / len(values)


def date_ratio(column: ColumnMetadata) -> float:
    values = [str(value).strip() for value in column.sample if value not in (None, "")]
    if not values:
        return 0.0
    formats = ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%Y/%m/%d", "%Y-%m-%dT%H:%M:%S")
    valid = sum(any(_parses(value, fmt) for fmt in formats) for value in values)
    return valid / len(values)


def _parses(value: str, fmt: str) -> bool:
    try:
        datetime.strptime(value, fmt)
        return True
    except ValueError:
        return False


def compatibility_score(column: ColumnMetadata, field: FieldSpec) -> tuple[float, str | None]:
    if field.kind == "measure":
        ratio = numeric_ratio(column)
        return ratio, f"El {ratio:.0%} de los valores de muestra parecen numéricos."
    if field.kind == "time":
        ratio = date_ratio(column)
        return ratio, f"El {ratio:.0%} de los valores de muestra parecen fechas."
    return 0.8, "El contenido es compatible con un campo descriptivo o identificador."
