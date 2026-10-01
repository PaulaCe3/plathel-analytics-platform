# Decisiones aceptadas

| Decisión | Aplicación / fuente |
|---|---|
| PLATHEL es la marca; DATA · AI · AUTOMATION es el descriptor. | [Sistema visual](../design_system_plathel.md). |
| Identidad Mineral/Mar, editorial y minimalista. | Jerarquía tipográfica, espacio y divisores finos; sin decoración dominante. |
| Dataviz verde musgo. | Aplicado en BI y forecast con los cinco tonos aprobados; valores en [Sistema visual](../design_system_plathel.md). |
| Space Grotesk + Inter. | Fuentes locales con licencias OFL en `packages/ui/fonts`. |
| BI y forecast separados internamente; experiencia unificada externamente. | [Arquitectura](../arquitectura_bi_multiindustria.md), shell compartido y fronteras import-linter. |
| Datos = preparar; Resultados = explicar; Dashboard = explorar. | Resultados es un resumen ejecutivo con máximo cuatro KPIs, tres hallazgos y predicción; no repite gráficos de exploración. |
| PLATHEL está diseñado para que clientes empresariales no técnicos puedan comprender sus datos sin conocimientos de Data Science, BI, estadística o Machine Learning. | Lenguaje empresarial adaptado al rubro mediante perfiles y terminología existentes. |
| PLATHEL hace la parte difícil; el cliente ve la parte fácil. | Detalles técnicos colapsados y decisiones visibles únicamente cuando requieren intervención. |
| Cross-filter y controles comparten un único estado de filtros. | Barras y alternativa tabular accesible generan FilterClause; backend recalcula y exporta el mismo contexto. |
| No duplicar ingestion, preparación ni sesiones. | Predicciones consume los datos ya preparados. |
| Backend calcula; frontend representa. | Contratos TypeScript generados desde OpenAPI, sin duplicar modelos. |
| No inventar predicciones ni interpretaciones. | Disponibilidad explícita, reglas determinísticas y limitaciones visibles; sin LLM. |
| GitHub conserva el historial del código y de la memoria. | `origin`: https://github.com/PaulaCe3/plathel-analytics-platform.git; rama actual `master`; sin force push. |
| Estos Markdown son memoria persistente del proyecto. | Fuente de verdad dentro del repositorio; enlazar documentación equivalente en lugar de copiarla. |
| Obsidian no añade una dependencia operativa. | Markdown estándar y enlaces internos; configuración personal `.obsidian/` excluida de Git. |

Actualizar solo decisiones que cambien o nuevas decisiones explícitamente aceptadas. Ver [[PRODUCT_VISION]] y [[CURRENT_STATE]].
