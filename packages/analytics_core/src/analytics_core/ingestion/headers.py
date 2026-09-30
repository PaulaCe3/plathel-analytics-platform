"""Structural header normalization without semantic interpretation."""

import re
from collections.abc import Iterable


def normalize_headers(values: Iterable[object]) -> tuple[list[str], list[str]]:
    original: list[str] = []
    normalized: list[str] = []
    counts: dict[str, int] = {}
    for position, value in enumerate(values, start=1):
        raw = "" if value is None else str(value)
        cleaned = re.sub(r"[\r\n]+", " ", raw.lstrip("\ufeff")).strip()
        base = cleaned or f"columna_{position}"
        counts[base] = counts.get(base, 0) + 1
        name = base if counts[base] == 1 else f"{base}_{counts[base]}"
        original.append(raw)
        normalized.append(name)
    return original, normalized


def stable_column_key(position: int) -> str:
    return f"c{position:02d}"
