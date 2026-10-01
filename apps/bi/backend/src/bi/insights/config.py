"""Documented noise guards for deterministic insights."""

GROWTH_MIN_ABS = 0.02
LEADER_MIN_SHARE = 0.30
LEADER_MIN_CATEGORIES = 3
CONCENTRATION_MIN_MEMBERS = 20
PEAK_MIN_PERIODS = 4
CHANNEL_MIN_CATEGORIES = 2
QUALITY_MIN_RATIO = 0.05
SUMMARY_LIMIT = 3
SECTION_LIMIT = 8

# Business candidates: normalized scores, never confidence estimates.
CHANGE_MIN_PP = 1.0
SEGMENT_MIN_WEIGHT = 0.02
TOP_N = 3
TOP_N_MIN_SHARE = 0.60
DECOMPOSITION_TOLERANCE = 1e-8
KIND_WEIGHT = {"change": 0.45, "leadership": 0.30, "concentration": 0.40,
               "segment_change": 0.35, "contribution": 0.55, "divergence": 0.65}
RELEVANCE_WEIGHT = 0.20
MAGNITUDE_WEIGHT = 0.35
# Only explicitly accepted mathematical relationships.
DIVERGENCE_PAIRS = (("revenue", "gross_margin_pct"),)
