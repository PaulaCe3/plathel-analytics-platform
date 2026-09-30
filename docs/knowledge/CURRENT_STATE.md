# Estado actual

Snapshot: 2026-09-30. Último checkpoint estable previo: `56d305d` (memoria), sobre implementación `26510bf`. Esta actualización acompaña `feat: implement simplified PLATHEL data journey`; su hash se consulta en Git para evitar referencias circulares.

Implementado: flujo **Datos → Resultados + Predicciones → Dashboard** de [[PRODUCT_VISION]]. Inicio centrado en CSV/XLSX con demos secundarios; columnas y preparación explícita dentro de Datos. Resultados muestra hasta cinco KPIs, hasta cuatro gráficos con interpretaciones del backend y predicción inicial automática cuando existe historial compatible. Dashboard prioriza un gráfico y dos secundarios, filtros, hallazgos, exploración y exportaciones. Dataviz verde musgo aplicada. Core y forecast siguen separados y comparten la sesión preparada.

Rutas: `/bi`, `/bi/[datasetId]/mapping`, `/bi/[datasetId]/review`, `/bi/[datasetId]/results`, `/bi/[datasetId]/dashboard`. `/forecast?dataset=<datasetId>` conserva compatibilidad. API y comandos: [README](../../README.md).

Validación de este cambio: 15 tests backend relevantes, 23 tests frontend y 17 escenarios E2E; lint, TypeScript, build, cuatro contratos import-linter y diff check. Dos recorridos críticos se repiten sobre el build visual final. Los recorridos incluyen accesibilidad automatizada y tamaños 1280/768/390px; capturas de Resultados y Dashboard revisadas en escritorio y móvil. Backend y contratos sin cambios.

Limitaciones: forecasting mensual necesita 24 meses completos consecutivos, horizonte de 1–6 meses desde el último observado y referencia anual; sin intervalos ni anticipación de tendencias. [Detalle](../../README.md#predicciones). No hay isotipo oficial. Axe no equivale a certificación exhaustiva de accesibilidad.

Siguiente tarea: ninguna adicional confirmada. Ver [[ROADMAP]].
