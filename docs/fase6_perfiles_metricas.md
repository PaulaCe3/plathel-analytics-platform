# Fase 6: perfiles y métricas

Los perfiles declaran su catálogo, orden de KPI, widgets e insights. `build_profile_registry` descubre `profiles/<id>/metrics.py` y crea un registro por solicitud. Todas las métricas usan Expr, availability, MetricEngine, QuerySpec y ComparisonResolver existentes.

- Retail: units_sold referencia quantity (alias de presentación, sin cálculo duplicado); total_cost, gross_profit, gross_margin_pct y average_discount.
- Servicios: service_hours y revenue_per_hour. Se conserva transactions, con su warning de fallback; no se presume un servicio por fila.
- Hotelería: total_nights, adr y average_stay (Mean(nights)). Sin nights quedan unavailable; no se deriva desde fechas ni se calcula ocupación.
- Custom: conserva las seis métricas universales, filtros y dimensiones custom. Las medidas custom se conservan sin clasificarlas como dimensiones ni generar métricas permanentes.

## Semánticas explícitas

Aunque ColumnMapping.options existe, canonical de Fase 3 no normaliza cost/discount según esas opciones. Fase 6 no cambia canonical ni raw. Por eso total_cost y sus dependientes solo se habilitan cuando el mapping de cost declara `options: {"basis": "total"}`. Costo unitario y costo sin metadata quedan unavailable con `reason_key=metric.requires_cost_basis_total`; si falta cost, se informa además missing_fields=["cost"]. No se infiere semántica por alias o nombre de columna.

average_discount es el promedio del importe de descuento por fila válida, con formato currency, únicamente con `options: {"kind": "amount"}`. Porcentajes y descuentos sin metadata quedan unavailable con reason explícito. No se inventa una escala porcentual. Estas opciones pueden enviarse mediante la API de mapping existente; no se agregó UI de normalización.

## Motor y dashboard

Las expresiones compuestas usan la intersección de filas válidas de todos sus operandos y reportan la unión de exclusiones. Cero en el denominador produce null/status empty. Las métricas monetarias y porcentajes de rentabilidad bloquean monedas mixtas, también en desgloses. Cada grupo se evalúa mediante MetricEngine; Otros se vuelve a evaluar sobre las filas restantes, incluso para promedios y ratios, sin sumar métricas no aditivas. La participación solo se informa para métricas aditivas.

Los KPI no disponibles se omiten y se explican en unavailable_metrics. Widgets específicos viven en industry_specific. Se agregaron tres aplicaciones de una regla de líder declarativa: categoría de retail, responsable de servicios y tipo de habitación. Usa revenue filtrado, al menos tres categorías y participación mínima de 30%; pasa por InsightEngine y elimina el hallazgo universal duplicado.

El frontend solo agrega labels, representación genérica de percent, textos de insights y razones semánticas; el contrato se genera desde OpenAPI. No se agregan componentes por industria ni funciones de Fase 7.
