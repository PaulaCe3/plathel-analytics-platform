# Decisiones aceptadas

| Decisión | Aplicación / fuente |
|---|---|
| PLATHEL es la marca; DATA · AI · AUTOMATION es el descriptor. | [Sistema visual](../design_system_plathel.md). |
| Identidad Mineral/Mar, editorial y minimalista. | Jerarquía tipográfica, espacio y divisores finos; sin decoración dominante. |
| Dataviz verde musgo. | Aplicado en BI y forecast con los cinco tonos aprobados; valores en [Sistema visual](../design_system_plathel.md). |
| Space Grotesk + Inter. | Fuentes locales con licencias OFL en `packages/ui/fonts`. |
| BI y forecast separados internamente; experiencia unificada externamente. | [Arquitectura](../arquitectura_bi_multiindustria.md), shell compartido y fronteras import-linter. |
| Flujo visible Datos → Resultados + Predicciones → Dashboard. | Preparación dentro de Datos; resultados integra forecast disponible; exploración y exportación en Dashboard. |
| No duplicar ingestion, preparación ni sesiones. | Predicciones consume los datos ya preparados. |
| Backend calcula; frontend representa. | Contratos TypeScript generados desde OpenAPI, sin duplicar modelos. |
| No inventar predicciones ni interpretaciones. | Disponibilidad explícita, reglas determinísticas y limitaciones visibles; sin LLM. |
| GitHub conserva el historial del código y de la memoria. | `origin`: https://github.com/PaulaCe3/plathel-analytics-platform.git; rama actual `master`; sin force push. |
| Estos Markdown son memoria persistente del proyecto. | Fuente de verdad dentro del repositorio; enlazar documentación equivalente en lugar de copiarla. |
| Obsidian no añade una dependencia operativa. | Markdown estándar y enlaces internos; configuración personal `.obsidian/` excluida de Git. |

Actualizar solo decisiones que cambien o nuevas decisiones explícitamente aceptadas. Ver [[PRODUCT_VISION]] y [[CURRENT_STATE]].
