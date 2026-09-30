# Fase 8 — Hardening y cierre técnico del MVP

## Alcance y auditoría

Se conservó el pipeline y las métricas de Fases 0–7. Working tree inicial limpio; baseline ejecutado: **140 tests backend + 5 frontend**. No se implementó V1.1 ni se hizo commit. La auditoría contra §§19–24 guio correcciones de gaps reales:

| Requisito | Inicial | Cierre |
|---|---|---|
| Contratos/core desacoplado, raw inmutable, export injection | DONE | DONE, regresión conservada |
| Upload: whitelist/NUL/falso XLSX/macros/traversal | PARTIAL | DONE, verificación por chunks/cuerpo completo |
| ZIP entries/expandido/ratio/OLE y XML seguro | PARTIAL | DONE, límites previos a openpyxl y defusedxml |
| TTL por inactividad y DELETE | DONE | DONE, lifecycle completo probado |
| TTL absoluto, purge inicial y reaper periódico | PARTIAL | DONE |
| Rate limiter, cupos y concurrencia | MISSING | DONE, un proceso |
| Profiling acotado y lectura de columnas Parquet | PARTIAL | DONE |
| Gráficos con una consulta por categoría | PARTIAL | DONE, agregación agrupada en una consulta |
| CORS y errores correlacionados | PARTIAL | DONE, métodos completos y errores sanitizados |
| Headers/CSP y trazas sin valores privados | PARTIAL | DONE, probado en producción |
| Responsive, aria, tabla de gráficos y foco | PARTIAL | DONE, axe/teclado/viewports |
| Tests frontend de estados/adaptadores | PARTIAL | DONE, infraestructura Node reutilizada |
| Playwright multi-industria/demo/downloads | MISSING | DONE, pipeline real |
| README/CI/deployment actualizados | MISSING | DONE |
| HSTS en HTTP local | NOT_APPLICABLE | Opt-in solo HTTPS producción |
| Servicios externos, autenticación, V1.1 | NOT_APPLICABLE | Fuera de alcance |

## Controles y decisiones

Límites centralizados: 20 MB archivo, 250.000 filas, 200 columnas, preview 50 (máximo 100), profiling 20.000, concurrencia pesada 2. ZIP: 1.000 entradas, 100 MB expandidos, ratio máximo 100:1 total y por entrada. Content-Length se controla temprano; un guard ASGI acota cuerpo completo antes de multipart, con spool temporal, y UploadSource limita el archivo real por chunks. Las filas sobre límite se rechazan sin truncar; se evita que una fila CSV más ancha se convierta silenciosamente en índice de pandas. XML usa defusedxml; openpyxl read_only/data_only/keep_links=False no ejecuta fórmulas.

Rate limit móvil de 3.600 segundos: 10 intentos de creación/upload/demo por IP. Cupos: 100 sesiones globales, 10 por IP. Headers de proxy se usan solo para peers exactos configurados. IPs viven únicamente en memoria; no en metadata/logs. DELETE/expire liberan cupos. Reinicio olvida rate history y ownership por IP; conserva conteo global por disco. Semáforo limita ingesta, canonical/validación, dashboard y export; operaciones livianas no ocupan ese cupo. Locks por sesión evitan reconstrucción/borrado simultáneos y reaper sobre sesiones activas.

TTL inactividad 60 minutos, absoluto 240; accesos válidos renuevan hasta el tope absoluto. Purge al iniciar y cada 120 segundos. CSV source se elimina después de parsear; XLSX source se conserva en parsed para cambios de hoja/configuración y se elimina al confirmar mapping. Raw se mantiene inmutable; canonical se reconstruye con acciones explícitas. TTL/DELETE eliminan todos los artefactos. Metadata atómica y rutas opacas validadas/resolve; permisos 0700/0600 donde el SO lo permite. Carpeta opaca sin metadata tiene gracia de 60 segundos para no borrar una creación en curso.

Se conserva la neutralización de fórmulas en headers/textos/auditoría/resumen de CSV/XLSX, sin modificar negativos numéricos. No se calculan KPIs sobre muestras: smoke generado de 2.000 filas y conceptos distintos verifica total completo y bucket Otros. Profiling es determinista y acotado; queries proyectan columnas necesarias. Expresiones existentes se evalúan sobre agregados agrupados para evitar lecturas por cada categoría, incluyendo ratios y promedios; no se agregaron métricas.

CORS explícito sin credentials, preflight POST/PUT/DELETE probado, Content-Disposition/X-Request-ID expuestos. Frontend: CSP, nosniff, no-referrer, DENY y Permissions-Policy; HSTS opt-in solo HTTPS producción. CSP mantiene inline scripts/styles por Next.js/ECharts; eval solo en desarrollo. Producción se probó con CSP activa y sin errores de JavaScript.

Errores esperables usan AppError; errores desconocidos devuelven INTERNAL_ERROR/500/request_id. Traces server-side contienen funciones/líneas/tipo, excluyendo mensajes que podrían incluir celdas o paths. Logs usan rutas parametrizadas y campos seguros, sin filename, preview, filtros, cuerpo ni filas. Timings JSON: sniff/read_raw/build_canonical/validate/query/export; rows/columns cuando están disponibles, null durante etapas sin tamaño resuelto. Query informa filas agregadas; export/validate informan su población. Health sigue barato y sin paths/configuración privada.

## Frontend y accesibilidad

Grid de 12: KPI span 12 móvil, 6 tablet, 3 desktop; gráficos fluidos con ResizeObserver y altura mínima. Tablas con scroll propio, mapping apilable, filtros colapsables y foco visible. ECharts aria/decal, título y leyenda textual, alternativa “Ver como tabla” con los mismos puntos agregados, sin recalcular métricas. Comparaciones conservan signo/valor/texto; issues muestran severidad textual. Loading/error/success importantes anuncian estados; el fallo al aplicar un filtro permite reintentar sin exportar resultados desactualizados.

Catálogo ligero es-AR para textos funcionales, métricas y campos; no se agregó next-intl ni otro idioma. Parsing de SourceSettings se conserva separado de Intl/presentación; mixed currency sigue protegida sin FX. Acción de borrado disponible durante el flujo, limpia estado/selección y vuelve a entrada con confirmación. Sesión expirada/no encontrada redirige con explicación. No se usa localStorage para contenido de sesiones; downloads revocan Object URLs.

## Verificación ejecutada

- Backend completo: **183 tests**; advertencia heredada de Starlette/httpx TestClient, sin fallos.
- Import-linter: **2 contratos conservados**; tests de contrato controlan pandas/numpy confinado y perfiles desacoplados.
- Frontend: **18 tests Node** sobre helpers reales, renderer, KPI, estados, tabla y adaptadores; lint/TypeScript/build.
- Playwright/axe: **6 tests de producción**. Retail propio, Servicios propio, Hotelería propia con moneda mixta, demo real, sesión no disponible y reintento de filtros. Los flujos reales cubren mapping/review/cleaning/dashboard/filtros/CSV/XLSX/DELETE; axe cubre entrada, mapping, review, dashboard y export UI sin desactivar reglas. XLSX inspeccionado con openpyxl; CSV no vacío, headers y filas esperadas. Viewports 390/768/1280 y controles por teclado.
- Seguridad: tamaños declarados/reales/cuerpo chunked, filas/columnas, NUL tardío, firmas falsas, XLSX falso, macros/externalLinks/OLE, ZIP ratio/entries/expandido, XML entity, traversal, rate/cupos/proxy, TTL/reaper/DELETE, concurrencia, CORS y errores/logs sin datos. Export injection conserva tests completos de Fase 7.
- OpenAPI regenerado a TypeScript; ErrorResponse deja de duplicarse manualmente. CI agrega comprobación de contrato generado, frozen install, frontend tests/typecheck y job E2E de producción.
- Dependencias: defusedxml y Playwright/axe como cambios mínimos; sin upgrades mayores ni dependencias accidentales. `pip check` pasó. `pnpm audit --json` se intentó y terminó con `fetch failed`: revisión externa de vulnerabilidades no disponible por red, **no certificada**.
- Secret scan de archivos versionados/nuevos: sin candidatos de claves/tokens/private keys/connection strings ni `.env` reales trackeados. `.env.example` solo configuración no secreta; `.gitignore` cubre env y artefactos temporales.

Smoke visual adicional en navegador: demo Retail, revisión y confirmación explícita de limpieza, dashboard con gráficos y métricas; filtro Canal Online (8 filas, ingresos 176.000) y DELETE con confirmación. Se corrigió la presentación de hallazgos: plantillas es-AR en lugar de claves internas/JSON; los parámetros y cálculos del backend se conservan.

## Riesgos residuales y deployment

Ver [guía de deployment](deployment_mvp.md) y [README reproducible](../README.md). Un worker persistente con disco temporal, memoria dimensionada y HTTPS; no serverless aislado ni varias réplicas. Proxy limita body/tiempos/conexiones, sobrescribe XFF si se declara confiable, y no conserva access logs con datos/IPs. Windows usa ACLs: configurar usuario/carpeta privada; chmod no ofrece semántica POSIX completa.

No hay autenticación: el enlace de sesión es una capacidad temporal y debe mantenerse privado. CSP no utiliza nonces y conserva inline. Pandas trabaja en memoria: los límites no son un SLA ni protección contra ataques distribuidos; reducirlos según recursos. ZIP altamente comprimido legítimo puede rechazarse. El semáforo no introduce timeout de trabajos; una operación activa puede posponer el purge hasta liberar su lock. Borrado es lógico del filesystem, no garantía forense/secure erase. Después de purge, expired no puede distinguirse de not found. Auditoría externa de dependencias queda pendiente de conectividad.

No se implementaron inventario/ocupación, IntervalSum, MRR/ARR, nuevas industrias, heatmaps/geografía, paginación server-side, PDF, auth/roles/billing, DB/cloud/Redis/colas/microservicios, telemetría externa, IA/LLM ni modelos analíticos de V1.1.
