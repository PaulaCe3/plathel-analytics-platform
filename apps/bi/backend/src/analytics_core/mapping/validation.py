"""Generic mapping validation independent from any concrete profile."""

from analytics_core.canonical.fields import FieldSpec
from analytics_core.ingestion.models import ColumnMetadata
from analytics_core.mapping.compatibility import date_ratio, numeric_ratio
from analytics_core.mapping.models import ColumnDisposition, ColumnMapping, MappingConflict


def validate_mapping(
    mappings: list[ColumnMapping],
    columns: list[ColumnMetadata],
    fields: list[FieldSpec],
    required_fields: set[str],
    *,
    max_custom_dimensions: int,
    max_custom_measures: int,
) -> list[MappingConflict]:
    conflicts: list[MappingConflict] = []
    by_column = {column.key: column for column in columns}
    by_field = {field.id: field for field in fields}
    seen_targets: dict[str, str] = {}
    seen_columns: set[str] = set()
    for mapping in mappings:
        if mapping.column_key not in by_column:
            conflicts.append(MappingConflict(code="COLUMN_NOT_FOUND", severity="error", message="La columna no existe.", column_key=mapping.column_key))
            continue
        if mapping.column_key in seen_columns:
            conflicts.append(MappingConflict(code="COLUMN_DUPLICATED", severity="error", message="La columna aparece más de una vez en el mapping.", column_key=mapping.column_key))
        seen_columns.add(mapping.column_key)
        if mapping.disposition != ColumnDisposition.canonical:
            continue
        target = mapping.target_field or ""
        if target not in by_field:
            conflicts.append(MappingConflict(code="FIELD_NOT_IN_PROFILE", severity="error", message="El campo no pertenece al perfil seleccionado.", column_key=mapping.column_key, field_id=target))
            continue
        if target in seen_targets:
            conflicts.append(MappingConflict(code="DUPLICATE_TARGET", severity="error", message="Dos columnas apuntan al mismo campo.", column_key=mapping.column_key, field_id=target))
        seen_targets[target] = mapping.column_key
        field = by_field[target]
        column = by_column[mapping.column_key]
        if field.kind == "measure" and numeric_ratio(column) < 0.6:
            conflicts.append(MappingConflict(code="MEASURE_INCOMPATIBLE", severity="error", message="La columna no parece numérica.", column_key=column.key, field_id=target))
        if field.kind == "time" and date_ratio(column) < 0.6:
            conflicts.append(MappingConflict(code="TIME_INCOMPATIBLE", severity="error", message="La columna no parece contener fechas.", column_key=column.key, field_id=target))
    for required in sorted(required_fields - set(seen_targets)):
        conflicts.append(MappingConflict(code="REQUIRED_FIELD_MISSING", severity="error", message="Falta un campo requerido.", field_id=required))
    custom_dimensions = sum(item.disposition == ColumnDisposition.custom_dimension for item in mappings)
    custom_measures = sum(item.disposition == ColumnDisposition.custom_measure for item in mappings)
    if custom_dimensions > max_custom_dimensions:
        conflicts.append(MappingConflict(code="CUSTOM_DIMENSION_LIMIT", severity="error", message=f"Se permiten hasta {max_custom_dimensions} dimensiones personalizadas."))
    if custom_measures > max_custom_measures:
        conflicts.append(MappingConflict(code="CUSTOM_MEASURE_LIMIT", severity="error", message=f"Se permiten hasta {max_custom_measures} medidas personalizadas."))
    return conflicts
