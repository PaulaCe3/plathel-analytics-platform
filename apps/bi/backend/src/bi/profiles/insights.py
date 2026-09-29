"""Small configured leader rule, using filtered revenue aggregates."""
from bi.insights.rules.universal import leader_share
from bi.insights.engine import Insight


def industry_leader(profile, points):
    # The first featured dimension defines the industry's headline breakdown.
    dimension = profile.bi.featured_dimensions[0] if profile.bi and profile.bi.featured_dimensions else None
    candidates = leader_share(points.get(dimension, []), dimension) if dimension else []
    terms = profile.data.terminology.get("es", {})
    return [Insight(id=f"industry_leader:{dimension}", rule_id="industry_leader", severity="neutral", template_key="insight.industry_leader", params=item.params, text=f"{terms.get(dimension, dimension)} líder en ingresos: {item.params['value']} ({item.params['share']:.1%}).", metric_id="revenue", dimension=dimension, score=item.score + .01) for item in candidates]
