# Estado actual

Snapshot: 2026-09-30. Último checkpoint estable previo: `883e7b5` — `feat: refine PLATHEL results and interactive dashboard`, subido a `origin/master`. Esta actualización acompaña `refactor: simplify PLATHEL information architecture`; su hash se consulta en Git.

Implementado: Datos prepara; Resultados explica; Dashboard permite explorar. Resultados ofrece una lectura narrativa con hasta dos números, tres hallazgos y predicción integrada. Dashboard presenta hasta cinco KPIs disponibles, evolución y un único desglose con selector; las interpretaciones locales no repiten hallazgos generales. Filtros compactos, chips activos y Limpiar comparten estado con barras y tablas accesibles. Exportar está junto al título y conserva el contexto mostrado. Opciones agrupa revisión, privacidad y borrado; Sobre estos datos mantiene calidad y limitaciones colapsadas. Se omiten secciones vacías y estados sin acción útil.

Los ejemplos visibles son Retail, Servicios y Hotelería. Retail utiliza internamente `retail_forecast_demo`: 108 registros sintéticos y 36 meses consecutivos, con ingestión, preparación y predicción reales. No hay botón independiente de historial. Preparación resume mejoras relevantes y conserva confirmación explícita para acciones destructivas. Forecast muestra fechas legibles, historial y futuro discontinuo e interpretación humana; metodología y evaluación quedan colapsadas.

Rutas: `/bi`, `/bi/[datasetId]/mapping`, `/bi/[datasetId]/review`, `/bi/[datasetId]/results`, `/bi/[datasetId]/dashboard`; `/forecast?dataset=<datasetId>` conserva compatibilidad. API y comandos: [README](../../README.md).

Validación: 16 tests backend relevantes, 26 frontend y 19 escenarios E2E distintos; tres recorridos críticos repetidos sobre el build final. Lint, TypeScript, build, cuatro contratos import-linter y diff check. Capturas de Datos, preparación, Resultados y Dashboard revisadas en escritorio y móvil; recorridos axe y responsive 1280/768/390px. No cambian arquitectura ni contratos API.

Limitaciones: forecast mensual requiere 24 meses completos consecutivos y estima 1–6 meses desde el último observado; no ofrece intervalos ni anticipa cambios de tendencia. La demo es histórica y sintética, no una proyección del calendario actual. Cross-filter requiere una dimensión filtrable identificada por el contrato; no aplica a series temporales ni al grupo Otros. Controles globales y tablas conservan la alternativa de teclado. Axe no constituye certificación exhaustiva.

Siguiente tarea: ninguna adicional confirmada. Ver [[ROADMAP]].
