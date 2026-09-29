"""Pandas query execution; dataframe objects remain confined to this package."""

from datetime import date, datetime
from typing import Any

import pandas as pd

from analytics_core.engine.query import DateCoverage, FilterClause, GroupBy, MeasureSpec, QueryResult, QuerySpec


def _native(value: Any):
    if pd.isna(value):
        return None
    if hasattr(value, "item"):
        value = value.item()
    if isinstance(value, pd.Timestamp):
        return value.to_pydatetime()
    return value


def _apply_filter(frame: pd.DataFrame, clause: FilterClause) -> pd.DataFrame:
    if clause.field not in frame:
        return frame.iloc[0:0]
    series = frame[clause.field]
    values = clause.values
    if clause.op == "in":
        mask = series.isin(values)
    elif clause.op == "not_in":
        mask = ~series.isin(values)
    elif clause.op == "between":
        mask = series.between(values[0], values[1], inclusive="both")
    elif clause.op == "gte":
        mask = series >= values[0]
    elif clause.op == "lte":
        mask = series <= values[0]
    else:
        mask = series.astype("string").str.contains(str(values[0]), case=False, regex=False, na=False)
    return frame.loc[mask.fillna(False)]


def _group_series(series: pd.Series, group: GroupBy) -> pd.Series:
    if group.grain is None:
        return series
    dates = pd.to_datetime(series, errors="coerce")
    if group.grain == "day":
        return dates.dt.strftime("%Y-%m-%d")
    if group.grain == "week":
        return dates.dt.to_period("W-SUN").dt.start_time.dt.strftime("%Y-%m-%d")
    if group.grain == "month":
        return dates.dt.to_period("M").astype("string")
    if group.grain == "quarter":
        return dates.dt.to_period("Q").astype("string")
    return dates.dt.to_period("Y").astype("string")


def _valid_rows(frame: pd.DataFrame, measure: MeasureSpec) -> tuple[pd.DataFrame, int]:
    mask = pd.Series(True, index=frame.index)
    for field in measure.required_fields:
        if field not in frame:
            return frame.iloc[0:0], len(frame)
        validity = f"_valid__{field}"
        if validity in frame:
            mask &= frame[validity].fillna(False).astype(bool)
        mask &= frame[field].notna()
        if pd.api.types.is_string_dtype(frame[field].dtype):
            mask &= frame[field].astype("string").str.strip().ne("").fillna(False)
    return frame.loc[mask], int((~mask).sum())


def _aggregate(frame: pd.DataFrame, measure: MeasureSpec, groups: list[str]):
    if measure.aggregation == "count":
        return frame.groupby(groups, dropna=False).size() if groups else len(frame)
    if measure.aggregation == "row_mul_sum":
        left, right = measure.fields or ("", "")
        values = frame[left] * frame[right]
    else:
        values = frame[measure.field or ""]
    if groups:
        grouped = values.groupby([frame[group] for group in groups], dropna=False)
        operation = "nunique" if measure.aggregation == "count_distinct" else measure.aggregation
        if operation == "sum":
            return grouped.sum(min_count=1)
        return getattr(grouped, operation)()
    if measure.aggregation == "count_distinct":
        return values.nunique(dropna=True)
    if measure.aggregation in {"sum", "row_mul_sum"}:
        return values.sum(min_count=1)
    return getattr(values, measure.aggregation)()


def run_query(canonical_path, query: QuerySpec) -> QueryResult:
    frame = pd.read_parquet(canonical_path)
    for clause in query.filters:
        frame = _apply_filter(frame, clause)
    group_names: list[str] = []
    for index, group in enumerate(query.group_by):
        name = group.field if group.grain is None else f"{group.field}__{group.grain}"
        frame[name] = _group_series(frame[group.field], group) if group.field in frame else None
        group_names.append(name)

    result: pd.DataFrame | None = None
    excluded: dict[str, int] = {}
    for measure in query.measures:
        valid, count = _valid_rows(frame, measure)
        excluded[measure.alias] = count
        aggregated = _aggregate(valid, measure, group_names)
        if group_names:
            part = aggregated.rename(measure.alias).reset_index()
            result = part if result is None else result.merge(part, on=group_names, how="outer")
        else:
            if result is None:
                result = pd.DataFrame([{}])
            result[measure.alias] = [_native(aggregated)]
    if result is None:
        result = frame[group_names].drop_duplicates() if group_names else pd.DataFrame([{}])

    for order in reversed(query.order_by):
        if order.field in result:
            result = result.sort_values(order.field, ascending=order.direction == "asc", na_position="last", kind="stable")
    if query.limit is not None and len(result) > query.limit:
        selected = result.iloc[:query.limit].copy()
        if query.others_bucket and len(group_names) == 1:
            other = {group_names[0]: "Otros"}
            chosen = selected[group_names[0]].tolist()
            remainder = frame.loc[~frame[group_names[0]].isin(chosen)]
            for measure in query.measures:
                valid, _ = _valid_rows(remainder, measure)
                other[measure.alias] = _native(_aggregate(valid, measure, []))
            selected = pd.concat([selected, pd.DataFrame([other])], ignore_index=True)
        result = selected
    records = [{key: _native(value) for key, value in row.items()} for row in result.to_dict(orient="records")]
    columns = [*group_names, *(measure.alias for measure in query.measures)]
    return QueryResult(columns=columns, rows=records, row_count=len(records), excluded_rows=excluded)


def date_coverage(canonical_path, field: str) -> DateCoverage:
    frame = pd.read_parquet(canonical_path, columns=[field])
    values = pd.to_datetime(frame[field], errors="coerce").dropna()
    if values.empty:
        return DateCoverage()
    return DateCoverage(minimum=values.min().date(), maximum=values.max().date())
