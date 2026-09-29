"""Confirmed dataframe transformations; every mutation returns an audit record."""

import pandas as pd

from analytics_core.cleaning.models import CleaningActionSpec, Transformation, TransformationExample


def apply_actions(frame: pd.DataFrame, actions: list[CleaningActionSpec], start_seq: int) -> tuple[pd.DataFrame, list[Transformation]]:
    result = frame.copy()
    transformations: list[Transformation] = []
    seq = start_seq
    for action in actions:
        if action.id in {"parse_dates", "parse_numbers"}:
            continue
        before_rows = len(result)
        affected = 0
        columns: list[str] = []
        examples: list[TransformationExample] = []
        kind = "normalize"
        if action.id == "trim_whitespace":
            for column in [name for name in result.columns if not name.startswith("_") and (pd.api.types.is_string_dtype(result[name].dtype) or result[name].dtype == object)]:
                original = result[column].astype("string")
                trimmed = original.str.strip()
                changed = original.fillna("") != trimmed.fillna("")
                if changed.any():
                    columns.append(column)
                    affected += int(changed.sum())
                    for row_id in result.loc[changed, "_row_id"].head(max(0, 3 - len(examples))).tolist():
                        index = result.index[result["_row_id"] == row_id][0]
                        examples.append(TransformationExample(row_id=int(row_id), before=str(original.loc[index]), after=str(trimmed.loc[index])))
                    result[column] = trimmed
        elif action.id == "drop_empty_columns":
            empty = [name for name in result.columns if not name.startswith("_") and _is_empty(result[name])]
            related_masks = [f"_valid__{name}" for name in empty if f"_valid__{name}" in result]
            result = result.drop(columns=[*empty, *related_masks])
            columns = empty
            affected = len(empty)
            kind = "remove"
        elif action.id == "drop_exact_duplicates":
            comparable = [name for name in result.columns if name != "_row_id" and not name.startswith("_valid__")]
            duplicate = result.duplicated(subset=comparable, keep="first")
            affected = int(duplicate.sum())
            examples = [TransformationExample(row_id=int(value)) for value in result.loc[duplicate, "_row_id"].head(3)]
            result = result.loc[~duplicate].copy()
            kind = "remove"
        elif action.id == "drop_rows":
            row_ids = {int(value) for value in action.params.get("row_ids", [])}
            selected = result["_row_id"].isin(row_ids)
            affected = int(selected.sum())
            examples = [TransformationExample(row_id=int(value)) for value in result.loc[selected, "_row_id"].head(3)]
            result = result.loc[~selected].copy()
            kind = "remove"
        seq += 1
        transformations.append(Transformation(id=f"t{seq:03d}", seq=seq, action_id=action.id, kind=kind, columns=columns, params=action.params, rows_before=before_rows, rows_after=len(result), rows_affected=affected, summary=_summary(action.id, affected), examples=examples[:3], automatic=False))
    return result, transformations


def _summary(action_id: str, affected: int) -> str:
    labels = {"trim_whitespace": "valores con espacios normalizados", "drop_empty_columns": "columnas vacías eliminadas", "drop_exact_duplicates": "filas duplicadas eliminadas", "drop_rows": "filas seleccionadas eliminadas"}
    return f"{affected} {labels.get(action_id, 'elementos procesados')}."


def _is_empty(series: pd.Series) -> bool:
    if bool(series.isna().all()):
        return True
    if pd.api.types.is_string_dtype(series.dtype) or series.dtype == object:
        return bool((series.isna() | series.astype("string").str.strip().eq("").fillna(False)).all())
    return False
