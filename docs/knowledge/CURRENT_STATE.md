# Estado actual

Snapshot: 2026-09-30. Último commit estable de implementación: `26510bf` — `feat: add PLATHEL analysis and forecasting experience`, subido a `origin/master`. Checkpoint previo: `9675734`. El commit de esta memoria y posteriores se consultan en Git, sin referencias circulares al propio archivo.

Implementado: carga CSV/XLSX, revisión de columnas, preparación explícita, análisis por industria, filtros, gráficos clave e interpretaciones determinísticas, hallazgos, exportaciones CSV/XLSX y sesiones temporales. Predicciones reutiliza datos preparados y muestra disponibilidad, estimación mensual, evaluación y límites. Core y UI compartidos, productos separados.

Rutas: `/bi`, `/bi/[datasetId]/mapping`, `/bi/[datasetId]/review`, `/bi/[datasetId]/dashboard`, `/forecast?dataset=<datasetId>`. Entrada de predicciones: `/forecast`. API y comandos: [README](../../README.md).

Validación ejecutada del último cambio de producto: 191 tests backend, 23 frontend y 17 escenarios E2E aprobados; tres flujos críticos repetidos sobre el build final. Lint, TypeScript, build, cuatro contratos import-linter y diff check pasan. Esta tarea de memoria no modifica código ejecutable.

Limitaciones: forecasting mensual con 24 meses completos consecutivos, horizonte de 1–6 meses desde el último observado y referencia anual; sin intervalos ni anticipación de tendencias. [Detalle](../../README.md#predicciones). Revisión visual manual previa parcial por bloqueo del navegador integrado; axe no equivale a certificación exhaustiva. No hay isotipo oficial. Dataviz aún mineral, no verde musgo. Los tres momentos definitivos de [[PRODUCT_VISION]] todavía no sustituyen el flujo visible actual.

Siguiente tarea confirmada: alinear la experiencia con [[PRODUCT_VISION]] y la dataviz verde musgo; sin implementación en esta tarea de memoria. Alcance pendiente en [[ROADMAP]].
