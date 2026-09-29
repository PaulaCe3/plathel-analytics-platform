"""Generic column mapping primitives."""

from analytics_core.mapping.matcher import suggest_mappings
from analytics_core.mapping.models import ColumnMapping, MappingConflict, MappingSuggestion

__all__ = ["ColumnMapping", "MappingConflict", "MappingSuggestion", "suggest_mappings"]
