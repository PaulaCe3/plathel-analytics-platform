# Arquitectura — mapa de consulta

La fuente oficial detallada sigue siendo [arquitectura_bi_multiindustria.md](arquitectura_bi_multiindustria.md). Buscar el encabezado con `rg -n` y leer solo la sección pertinente; no cargar el documento completo. Describe diseño y contratos, incluidas propuestas futuras: contrastar la funcionalidad con [CURRENT_STATE.md](knowledge/CURRENT_STATE.md) y la implementación existente. El prompt determina el alcance autorizado.

## Invariantes
- `analytics_core` nunca importa `bi`; BI y forecast no se importan entre sí. Agregar una industria no exige modificar el core.
- pandas/numpy solo pueden importarse dentro de `analytics_core/engine/pandas_impl/`.
- API: routers → services → core; routers sin lógica de negocio. Backend calcula; frontend renderiza.
- Contratos TypeScript generados desde FastAPI/OpenAPI; no duplicar modelos manualmente.
- `raw.parquet` es inmutable. canonical se reconstruye desde raw + mapping + configuración + acciones.
- Issue y Transformation son distintos; ninguna transformación de datos puede ser silenciosa.
- Reutilizar ingestión, preparación y sesiones. Sin infraestructura ni funcionalidades futuras no solicitadas.

## Secciones de la fuente oficial
| Tarea | Secciones a buscar |
|---|---|
| Estructura y dependencias | 1–3; core en `packages/analytics_core`, productos BI/forecast y composición `platform_api` |
| Canonical, perfiles, CSV/XLSX, mapping | 4–7 |
| Validación, limpieza y auditoría | 8 |
| DataEngine, QuerySpec y métricas | 9–10 |
| Comparaciones, filtros, dashboard e insights | 11–14 |
| Exportación, demo e interoperabilidad | 15 |
| API y contratos | 16–17 |
| Frontend y estado | 18 |
| Seguridad, tamaño, errores, región y accesibilidad | 19–22 |
| Testing y observabilidad | 23–24 |
| Planificación y límites de diseño | 25–27; consultar solo si la tarea lo requiere |

Comandos y estructura operativa: [README](../README.md). Decisiones de producto aceptadas: [DECISIONS.md](DECISIONS.md). La promoción del core y UI compartida ya está implementada; las recomendaciones históricas de la arquitectura no implican volver a carpetas anteriores.
