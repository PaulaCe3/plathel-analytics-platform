# Deployment MVP, seguridad y privacidad técnica

## Topología soportada

Backend FastAPI en proceso/contenedor persistente, **un solo worker**, con disco temporal exclusivo y escribible. No usar serverless aislado por request ni varios workers/réplicas: ownership por IP, rate limiter, semáforo y locks son in-memory. Los archivos de sesión viven en `DATASET_STORAGE_PATH`. El frontend puede desplegarse separado: `pnpm build` y `pnpm start`. No se agrega infraestructura a este repositorio.

Instalar dependencias backend con `pip install -e .`, frontend con `pnpm install --frozen-lockfile`. Ejecutar backend con `uvicorn bi.api.main:app --workers 1 --no-access-log --no-proxy-headers`. Deshabilitar access logs externos que registren URLs completas, filtros o IPs; los logs propios usan rutas parametrizadas y request_id. No respaldar sesiones temporales ni publicar `.data` como archivos estáticos.

## Entorno y proxy

Configurar los valores de ambos `.env.example`. Backend: `APP_ENV`, `FRONTEND_ORIGIN` o `CORS_ORIGINS` (lista JSON explícita), `DATASET_STORAGE_PATH`, límites de archivo/filas/columnas/ZIP, TTL, reaper, concurrencia y cupos. No usar `*` para CORS; no requiere credentials. `TRUSTED_PROXY_IPS` es una lista JSON vacía por defecto. Solo IPs exactas del proxy controlado deben incluirse; el proxy debe sobrescribir X-Forwarded-For. Mantener `--no-proxy-headers` en Uvicorn para que la aplicación valide el peer real.

Producción requiere HTTPS. Reverse proxy debe limitar cuerpo (20 MB más overhead multipart configurado), tiempos y conexiones; no confiar en Content-Length. El backend verifica tamaño real del archivo por chunks, además del chequeo temprano de Content-Length. Un guard ASGI limita también el cuerpo completo por chunks antes de FastAPI/Starlette, usando spool temporal cerrado al terminar. El proxy sigue siendo necesario para cuotas de conexiones, tiempos y defensa antes del proceso. Configurar el directorio temporal del sistema en disco privado con cuota.

Frontend: `NEXT_PUBLIC_API_BASE_URL` público se incorpora en build; `HTTPS_DEPLOYMENT=true` activa HSTS **solo en producción HTTPS**. La CSP restringe orígenes, frames y objetos; mantiene inline scripts/styles para Next.js/ECharts y eval únicamente en desarrollo. No es una CSP con nonces. Descargar blobs se probó con ella. Security headers: nosniff, no-referrer, DENY, Permissions-Policy; backend responde no-store.

## Límites efectivos

| Control | Default |
|---|---:|
| Archivo real | 20 MB |
| Filas / columnas | 250.000 / 200 |
| Preview default / máximo | 50 / 100 |
| Profiling máximo de filas | 20.000 |
| Operaciones pesadas simultáneas | 2 |
| Creaciones por IP, ventana móvil | 10 por 3.600 segundos |
| Sesiones globales / por IP | 100 / 10 |
| TTL inactividad / absoluto | 60 / 240 minutos |
| Reaper | inicio y cada 120 segundos |
| ZIP entradas / expandido / ratio | 1.000 / 100 MB / 100:1 |

Se cuentan intentos de creación/upload y `/datasets/demo`; no se limita navegación normal por esa ventana. DELETE/expire liberan cupo. Reiniciar conserva el cupo global en disco, pero olvida ownership/IPs y rate history. Es una limitación aceptada del MVP de un proceso. La caducidad en un acceso se distingue como DATASET_EXPIRED cuando todavía existe metadata; después del purge se informa DATASET_NOT_FOUND.

## Ciclo de vida real

Upload → `source.bin` opaco → `raw.parquet` → mapping/configuración/acciones → `canonical.parquet` → análisis/export. CSV source desaparece tras parsear; XLSX se mantiene solo en parsed para cambiar hoja/configuración y se elimina al guardar mapping. Raw no se transforma; el log explica las transformaciones de canonical. Sesión expirada se elimina en acceso o reaper; DELETE borra inmediatamente todo el directorio. Purge inicial limpia sesiones caducadas del proceso anterior y metadata corrupta; carpetas opacas sin metadata tienen una gracia de inicialización de 60 segundos. No se promete borrado físico irrecuperable ni cumplimiento legal/compliance.

Directorios de sesión 0700 y metadata 0600 cuando el SO lo soporta; Windows aplica sus ACLs, sin depender de chmod. Configurar ACLs y usuario dedicado del proceso. Los IDs son aleatorios y validados; resolve impide salir de raíz. El filename original no se usa como path. No hay autenticación: conocer la URL permite acceder a la sesión. HTTPS, privacidad de enlaces, restricciones de red y TTL son esenciales.

## Controles de archivo y export

Whitelist CSV/XLSX, controles de firma/binarios y NUL en todos los chunks, ZIP válido/estructura mínima, rutas ZIP, macros, externalLinks y embeddings/OLE rechazados antes de openpyxl. ZIP limitado por entradas, bytes expandidos y ratio total/por entrada. openpyxl utiliza defusedxml; entrada read_only/data_only/keep_links=False. Fórmulas no se ejecutan. Filas y columnas excedidas se rechazan sin truncar. El formato no admite todos los posibles archivos de Excel: libros extremadamente comprimidos legítimos pueden rechazarse por límites.

Export neutraliza caracteres de fórmula en headers, textos, auditoría y resumen; conserva negativos numéricos. CSV no crea archivos permanentes; XLSX se genera en memoria dentro del cupo de trabajo pesado. Logs no contienen celdas, filenames, previews, cuerpos ni filtros; trazas incluyen funciones/líneas/tipo, excluyendo mensajes de excepciones potencialmente sensibles. Al cliente llegan AppError/envelope, nunca una traza técnica. X-Request-ID se genera/sanea y correlaciona logs/respuesta.

## Operación y riesgos residuales

Health es barato y no enumera sesiones. Logs JSON incluyen endpoint, status, code y timings sniff/read_raw/build_canonical/validate/query/export. KPIs usan población completa; profiling se limita a muestras deterministas. Parquet proyecta columnas de consulta, y los gráficos agregan todas las categorías en una consulta para evitar crecimiento por categoría.

Pandas sigue procesando en memoria; 250.000 × 200 valores puede requerir mucha RAM aunque la carga sea 20 MB. Dimensionar memoria/disco y reducir límites según despliegue. Semáforo limita simultaneidad, no tiempo de ejecución; reaper evita borrar sesiones mientras una operación bloqueada por sesión está activa. No hay garantía frente a saturación distribuida, ataque sofisticado, acceso de otro usuario del host o caída del disco. No usar varios procesos sin rediseñar coordinación en una fase autorizada. Mantener revisión de dependencias y repetir E2E tras cambios de entorno.
