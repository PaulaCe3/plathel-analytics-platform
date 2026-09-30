"""Deterministic alias, fuzzy-name and sample compatibility matcher."""

import re
import unicodedata
from difflib import SequenceMatcher

from analytics_core.canonical.fields import FieldSpec
from analytics_core.ingestion.models import ColumnMetadata
from analytics_core.mapping.compatibility import compatibility_score, numeric_ratio
from analytics_core.mapping.models import ColumnDisposition, MappingCandidate, MappingSuggestion


def normalize_name(value: str) -> str:
    text = unicodedata.normalize("NFKD", value.lower().strip())
    text = "".join(character for character in text if not unicodedata.combining(character))
    return re.sub(r"[^a-z0-9]+", "_", text).strip("_")


def _confidence(score: float) -> str:
    return "high" if score >= 0.85 else "medium" if score >= 0.60 else "low"


def suggest_mappings(
    columns: list[ColumnMetadata],
    fields: list[FieldSpec],
    aliases: dict[str, list[str]],
) -> list[MappingSuggestion]:
    suggestions: list[MappingSuggestion] = []
    for column in columns:
        header = normalize_name(column.original_name)
        candidates: list[MappingCandidate] = []
        for field in fields:
            names = [field.id, *aliases.get(field.id, [])]
            normalized_aliases = [normalize_name(alias) for alias in names]
            exact = header in normalized_aliases
            best_alias = max(normalized_aliases, key=lambda alias: SequenceMatcher(None, header, alias).ratio())
            fuzzy = SequenceMatcher(None, header, best_alias).ratio()
            compatible, compatibility_reason = compatibility_score(column, field)
            score = min(1.0, (0.82 if exact else 0.58 * fuzzy) + 0.18 * compatible)
            reasons = [f"Coincide con alias «{best_alias}»." if exact else f"Nombre similar a «{best_alias}»."]
            if compatibility_reason:
                reasons.append(compatibility_reason)
            if exact or score >= 0.50:
                candidates.append(MappingCandidate(field_id=field.id, score=round(score, 3), confidence=_confidence(score), reasons=reasons))
        candidates.sort(key=lambda candidate: (-candidate.score, candidate.field_id))
        numeric = numeric_ratio(column)
        if numeric >= 0.8:
            disposition = ColumnDisposition.custom_measure
        elif column.approximate_cardinality and column.approximate_cardinality <= 50:
            disposition = ColumnDisposition.custom_dimension
        else:
            disposition = ColumnDisposition.ignored
        suggestions.append(MappingSuggestion(column_key=column.key, candidates=candidates[:3], suggested_disposition=disposition))
    return suggestions
