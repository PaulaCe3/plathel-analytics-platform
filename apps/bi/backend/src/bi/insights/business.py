"""Structured business facts over the same filtered metrics and F1 comparisons."""
import math
from bi.insights.config import (CHANGE_MIN_PP, DECOMPOSITION_TOLERANCE, DIVERGENCE_PAIRS,
    GROWTH_MIN_ABS, KIND_WEIGHT, MAGNITUDE_WEIGHT, RELEVANCE_WEIGHT, SEGMENT_MIN_WEIGHT,
    TOP_N, TOP_N_MIN_SHARE)
from bi.insights.engine import Insight, InsightEngine
from bi.metrics.models import MetricResult

METRIC_LABELS = {"transactions": "Operaciones", "customers": "Clientes",
    "avg_transaction_value": "Importe promedio", "quantity": "Cantidad",
    "avg_unit_price": "Precio promedio", "gross_profit": "Resultado bruto",
    "gross_margin_pct": "Margen bruto", "total_cost": "Costo total",
    "units_sold": "Unidades", "service_hours": "Horas de servicio",
    "revenue_per_hour": "Facturación por hora", "total_nights": "Noches",
    "adr": "Tarifa promedio", "average_stay": "Estadía promedio"}


def finite(value):
    return value is not None and math.isfinite(float(value))


def number(value):
    return f"{value:,.1f}".replace(",", "_").replace(".", ",").replace("_", ".")


def label(metric, profile):
    terms = profile.data.terminology.get("es", {})
    return terms.get(metric, terms.get("amount", "Importe") if metric == "revenue" else METRIC_LABELS.get(metric, "Valor"))


def changed(comparison):
    if comparison is None or comparison.status not in {"ok", "previous_zero"} or not finite(comparison.delta_abs):
        return False
    if comparison.delta_pp is not None:
        return abs(comparison.delta_pp) >= CHANGE_MIN_PP
    return abs(comparison.delta_pct) >= GROWTH_MIN_ABS if comparison.delta_pct is not None else comparison.delta_abs != 0


def change_text(comparison, currency=None):
    direction = "aumentó" if comparison.delta_abs > 0 else "disminuyó"
    if comparison.delta_pp is not None:
        amount = f"{number(abs(comparison.delta_pp))} pp"
    elif comparison.delta_pct is not None:
        amount = f"{number(abs(comparison.delta_pct)*100)} %"
    else:
        amount = f"{currency or ''} {number(abs(comparison.delta_abs))}".strip()
    return f"{direction} {amount} respecto del período anterior"


def candidate(kind, metric, profile, *, comparison=None, current=None, dimension=None, segment=None,
              share=None, contribution=None, magnitude=0, text, extra=None):
    order = profile.bi.kpi_order if profile.bi else ()
    relevance = 1 / (1 + order.index(metric)) if metric in order else 0
    params = {"current": current, "segment": segment, "share": share, "contribution": contribution}
    if comparison:
        params.update(baseline=comparison.previous_value, absolute_delta=comparison.delta_abs,
                      relative_delta=comparison.delta_pct, percentage_points=comparison.delta_pp,
                      period=comparison.model_dump(mode="json"))
    if extra: params.update(extra)
    if comparison and (comparison.partial_period or comparison.warnings):
        text += " Comparación con cobertura parcial."
    score = KIND_WEIGHT[kind] + RELEVANCE_WEIGHT*relevance + MAGNITUDE_WEIGHT*min(abs(magnitude), 1)
    return Insight(id=f"{kind}:{metric}:{dimension}:{segment}", rule_id=kind, kind=kind,
                   severity="neutral", template_key="business.fact", params=params, text=text,
                   metric_id=metric, dimension=dimension, score=score)


def business_insights(profile, registry, results, grouped, context):
    """grouped contains full, untruncated aggregates for current and previous filters."""
    found = []
    metrics = {r.metric_id: r for r in results if isinstance(r, MetricResult) and r.status == "ok" and finite(r.value)}
    for metric, result in metrics.items():
        c = result.comparison
        if changed(c):
            found.append(candidate("change", metric, profile, comparison=c, current=result.value,
                magnitude=c.delta_pct or (c.delta_pp or 0)/100,
                text=f"{label(metric, profile)} {change_text(c, result.format.currency)}."))
    for (metric, dimension), (current, previous, comparisons) in grouped.items():
        result = metrics.get(metric)
        if result is None: continue
        values = sorted([(k, v) for k, v in current.items() if k is not None and finite(v)], key=lambda x: (-x[1], str(x[0])))
        if len(values) < 2: continue
        total = result.value
        positive = (registry.get(metric).additive and total > 0
            and all(finite(v) and v >= 0 for v in current.values())
            and math.isclose(sum(current.values()), total, rel_tol=DECOMPOSITION_TOLERANCE, abs_tol=DECOMPOSITION_TOLERANCE))
        shares = {k: v/total for k, v in values} if positive else {}
        leader, value = values[0]
        # Ties do not identify a unique leader; "Otros" is never a real segment here.
        if value > values[1][1]:
            share = shares.get(leader)
            kind = "concentration" if share is not None and share >= TOP_N_MIN_SHARE else "leadership"
            noun = profile.data.terminology.get("es", {}).get(dimension, "Segmento")
            text = (f"{leader} concentra el {number(share*100)} % de {label(metric, profile).lower()}."
                    if kind == "concentration" else f"{noun}: {leader} tuvo el mayor valor de {label(metric, profile).lower()}: {result.format.currency or ''} {number(value)}.")
            found.append(candidate(kind, metric, profile, current=value, dimension=dimension, segment=str(leader),
                share=share, magnitude=share or 0, text=text))
        if positive and len(values) > TOP_N:
            share = sum(shares[k] for k, _ in values[:TOP_N])
            if share >= TOP_N_MIN_SHARE:
                found.append(candidate("concentration", metric, profile, dimension=dimension, share=share,
                    magnitude=share, text=f"Los {TOP_N} principales segmentos de {profile.data.terminology.get('es', {}).get(dimension, 'la dimensión').lower()} concentran el {number(share*100)} % de {label(metric, profile).lower()}.", extra={"top_n": TOP_N}))
        c = result.comparison
        # Reconciliation proves the entire partition, including null and negative groups.
        valid_partition = (c is not None and c.status in {"ok", "previous_zero"} and finite(c.delta_abs)
            and previous is not None and all(finite(v) for v in [*current.values(), *previous.values()])
            and math.isclose(sum(current.values()), total, rel_tol=DECOMPOSITION_TOLERANCE, abs_tol=DECOMPOSITION_TOLERANCE)
            and math.isclose(sum(previous.values()), c.previous_value, rel_tol=DECOMPOSITION_TOLERANCE, abs_tol=DECOMPOSITION_TOLERANCE))
        weight = sum(abs(v) for v in current.values()) + sum(abs(v) for v in (previous or {}).values())
        for segment, segment_comparison in comparisons.items():
            if segment is None or not changed(segment_comparison): continue
            value = current.get(segment)
            baseline = previous.get(segment) if previous is not None else None
            if not finite(value) or not finite(baseline) or not weight or (abs(value)+abs(baseline))/weight < SEGMENT_MIN_WEIGHT: continue
            found.append(candidate("segment_change", metric, profile, comparison=segment_comparison,
                current=value, dimension=dimension, segment=str(segment), magnitude=segment_comparison.delta_pct or 0,
                text=f"{segment}: {label(metric, profile).lower()} {change_text(segment_comparison, result.format.currency)}."))
        if valid_partition and registry.get(metric).additive and c.delta_abs != 0:
            for segment in sorted(set(current) | set(previous), key=str):
                if segment is None: continue
                delta = current.get(segment, 0) - previous.get(segment, 0)
                contribution = delta / c.delta_abs
                if not finite(contribution) or not weight or (abs(current.get(segment,0))+abs(previous.get(segment,0)))/weight < SEGMENT_MIN_WEIGHT or delta == 0: continue
                found.append(candidate("contribution", metric, profile, comparison=c, current=current.get(segment,0),
                    dimension=dimension, segment=str(segment), contribution=contribution, magnitude=abs(contribution),
                    text=f"{label(metric, profile)} cambió {result.format.currency or ''} {number(c.delta_abs)}; {segment} aportó {result.format.currency or ''} {number(delta)} ({number(contribution*100)} % del cambio neto).",
                    extra={"segment_delta": delta, "segment_baseline": previous.get(segment,0)}))
    for first, second in DIVERGENCE_PAIRS:
        a, b = metrics.get(first), metrics.get(second)
        if a and b and a.excluded_rows == 0 and b.excluded_rows == 0 and changed(a.comparison) and changed(b.comparison) and a.comparison.delta_abs*b.comparison.delta_abs < 0 and a.comparison.current_range == b.comparison.current_range and a.comparison.previous_range == b.comparison.previous_range and a.excluded_rows == b.excluded_rows:
            found.append(candidate("divergence", first, profile, comparison=a.comparison, current=a.value, magnitude=1,
                text=f"{label(first,profile)} {change_text(a.comparison,a.format.currency)}, mientras {label(second,profile).lower()} {change_text(b.comparison)}.", extra={"related_metric": second, "related_comparison": b.comparison.model_dump(mode="json")}))
    return InsightEngine().prioritize([item.model_copy(update={"params": {**item.params, "filters": context}}) for item in found])
