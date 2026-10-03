# Decisiones aceptadas

| Decisión | Aplicación / fuente |
|---|---|
| PLATHEL es la marca; DATA · AI · AUTOMATION es el descriptor. | [Sistema visual](DESIGN_SYSTEM.md). |
| Identidad Mineral/Mar, editorial y minimalista. | Jerarquía tipográfica, espacio y divisores finos; sin decoración dominante. |
| Dataviz verde musgo. | Moss `#4F5948` es el acento; la escala Mineral/Mar aporta contexto en BI y forecast. Valores en [Sistema visual](DESIGN_SYSTEM.md). |
| Space Grotesk + Inter. | Fuentes locales con licencias OFL en `packages/ui/fonts`. |
| BI y forecast separados internamente; experiencia unificada externamente. | [Arquitectura](arquitectura_bi_multiindustria.md), shell compartido y fronteras import-linter. |
| Datos = preparar; Resultados = explicar; Dashboard = explorar. | Resultados es una lectura narrativa con pocos números, hasta tres hallazgos y predicción; los KPIs y la exploración pertenecen a Dashboard. |
| PLATHEL está diseñado para que clientes empresariales no técnicos puedan comprender sus datos sin conocimientos de Data Science, BI, estadística o Machine Learning. | Lenguaje empresarial adaptado al rubro mediante perfiles y terminología existentes. |
| No mostrar estados, métricas o información técnica que no requieran acción ni ayuden al cliente a comprender su negocio. | Opciones y Sobre estos datos contienen detalles secundarios; se omiten secciones vacías. |
| Resultados prioriza comprensión; Dashboard prioriza exploración. No deben duplicar contenido. | Resumen narrativo frente a KPIs; interpretaciones locales deduplicadas de los hallazgos generales. |
| PLATHEL hace la parte difícil; el cliente ve la parte fácil. | Detalles técnicos colapsados y decisiones visibles únicamente cuando requieren intervención. |
| Acciones con impacto cero no se muestran. | Preparación omite filas/valores sin efecto y no crea Opciones avanzadas vacías; el registro también omite transformaciones sin efecto. |
| Moss `#4F5948` = datos, selección y estado correcto; Wine `#6B3037` = atención, error y destrucción. | Son microacentos sobre la identidad Mineral/Mar; negativos solo reciben color semántico cuando existe una interpretación segura. Tokens en [Sistema visual](DESIGN_SYSTEM.md). |
| La predicción integrada en Resultados es automática; la comparación de segmentos es secundaria. | Resultados oculta configuración de forecast y Dashboard revela comparación dentro de Más opciones; las vistas especializadas conservan sus controles. |
| Un CTA principal por decisión; detalles técnicos siempre secundarios. | Ajustes seguros separados de eliminación; conservar/eliminar es explícito y eliminar requiere confirmación. |
| No mostrar controles o información sin utilidad para el cliente. | Períodos rápidos usan la última fecha del archivo; Personalizado revela fechas manuales. Mismos filtros y exportación. |
| Cross-filter y controles comparten un único estado de filtros. | Barras y alternativa tabular accesible generan FilterClause; backend recalcula y exporta el mismo contexto. |
| No duplicar ingestion, preparación ni sesiones. | Predicciones consume los datos ya preparados. |
| Backend calcula; frontend representa. | Contratos TypeScript generados desde OpenAPI, sin duplicar modelos. |
| No inventar predicciones ni interpretaciones. | Disponibilidad explícita, reglas determinísticas y limitaciones visibles; sin LLM. |
| PLATHEL público usa exclusivamente datasets precargados; el visitante no carga datos propios. | La experiencia es elegir ejemplo → procesamiento automático → Resultados → Dashboard. Ingestión, upload, Autopilot, mapping, validación y limpieza permanecen internos para implementaciones reales. |
| GitHub conserva el historial del código y de la memoria. | `origin`: https://github.com/PaulaCe3/plathel-analytics-platform.git; rama actual `master`; sin force push. |
| Estos Markdown son memoria persistente del proyecto. | Fuente de verdad dentro del repositorio; enlazar documentación equivalente en lugar de copiarla. |
| Obsidian no añade una dependencia operativa. | Markdown estándar y enlaces internos; configuración personal `.obsidian/` excluida de Git. |

Actualizar solo decisiones que cambien o nuevas decisiones explícitamente aceptadas. Ver [visión de producto](CONTEXT.md) y [estado actual](knowledge/CURRENT_STATE.md).

