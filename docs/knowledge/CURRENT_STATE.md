# Estado actual

Snapshot: 2026-09-30. Último checkpoint estable previo: `c707098` — `feat: implement simplified PLATHEL data journey`, subido a `origin/master`. Esta actualización acompaña `feat: refine PLATHEL results and interactive dashboard`; su hash se consulta en Git.

Implementado: Datos prepara; Resultados explica; Dashboard permite explorar. Resultados presenta máximo cuatro KPIs en el orden del perfil, hasta tres hallazgos determinísticos y forecast integrado, sin gráficos descriptivos repetidos. Dashboard mantiene filtros globales, gráfico principal y dos secundarios; Explorar por sustituye una visual secundaria. Barras compatibles y botones de tabla filtran el mismo estado; chips permiten quitar filtros y Ver todo reinicia. Backend recalcula métricas, gráficos, hallazgos e interpretaciones; exportación conserva el contexto mostrado.

Demo nueva `retail_forecast_demo`: 108 registros sintéticos y 36 meses consecutivos, con ingestión, preparación, análisis y predicción reales. Se ofrece dentro de los ejemplos de Datos. Forecast muestra fechas legibles, historial y futuro discontinuo, evaluación explicada y límites; detalles técnicos colapsados. Lenguaje adaptado por perfiles, sin siglas ADR en la interfaz principal.

Rutas: `/bi`, `/bi/[datasetId]/mapping`, `/bi/[datasetId]/review`, `/bi/[datasetId]/results`, `/bi/[datasetId]/dashboard`; `/forecast?dataset=<datasetId>` conserva compatibilidad. API y comandos: [README](../../README.md).

Validación: 37 tests backend relevantes, 24 frontend, 19 escenarios E2E distintos; siete recorridos afectados se verifican sobre el build final. Lint, TypeScript, build, cuatro contratos import-linter y diff check. Tras el ajuste final del selector y la jerarquía, tres recorridos críticos se vuelven a comprobar. Capturas de Datos, Resultados con predicción y Dashboard revisadas en escritorio y móvil; recorridos axe y responsive 1280/768/390px. No cambia la arquitectura ni los contratos API.

Limitaciones: forecast mensual requiere 24 meses completos consecutivos y estima 1–6 meses desde el último observado; no ofrece intervalos ni anticipa cambios de tendencia. La demo es histórica y sintética, no una proyección del calendario actual. Cross-filter se habilita cuando el contrato identifica una dimensión filtrable; no aplica a series temporales ni al grupo agregado Otros. Controles globales y tablas conservan la alternativa de teclado. Axe no constituye certificación exhaustiva.

Siguiente tarea: ninguna adicional confirmada. Ver [[ROADMAP]].
