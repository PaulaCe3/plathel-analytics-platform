"""Cleaning action catalog and request validation."""

from analytics_core.cleaning.models import CleaningActionSpec

ACTION_IDS = {"trim_whitespace", "parse_dates", "parse_numbers", "drop_empty_columns", "drop_exact_duplicates", "drop_rows"}
DESTRUCTIVE_ACTIONS = {"drop_empty_columns", "drop_exact_duplicates", "drop_rows"}


def validate_action_ids(actions: list[CleaningActionSpec]) -> None:
    unknown = {action.id for action in actions} - ACTION_IDS
    if unknown:
        raise ValueError(f"unknown cleaning actions: {sorted(unknown)}")
