# DATA SIGHT BI Multi-Industria

MVP de Business Intelligence para Retail / E-commerce, Servicios, Hotelería y perfil personalizado. Permite cargar CSV/XLSX, confirmar el significado de columnas, revisar calidad y transformaciones, filtrar dashboards y exportar CSV/XLSX. Fases 0–8; no incorpora V1.1.

## Arquitectura y estructura

La fuente de verdad es [la arquitectura oficial](docs/arquitectura_bi_multiindustria.md). `analytics_core` contiene ingesta, sesiones, canonical, validación, consultas y exports; nunca importa `bi`. Pandas/numpy quedan confinados a `engine/pandas_impl`. `bi` declara perfiles, métricas, dashboards e insights. API: routers → services → core. Frontend Next.js/ECharts renderiza resultados calculados en backend; sus contratos se generan desde OpenAPI.

- `apps/bi/backend/src/analytics_core/`: motor genérico.
- `apps/bi/backend/src/bi/`: producto y API.
- `apps/bi/backend/demo_data/`: demos sintéticas y mapping versionado.
- `apps/bi/backend/tests/`: unitarios, integración y contratos.
- `apps/bi/frontend/src/`: UI y contratos generados.
- `apps/bi/frontend/tests/`: tests Node y Playwright/axe.
- `docs/`: arquitectura, fases, deployment y hardening.

## Requisitos e instalación

Python 3.12+, Node.js 24 y pnpm 11.19.0. Backend necesita disco local temporal. Comandos PowerShell; en Linux usar `source .venv/bin/activate` y `cp` para copiar archivos.

```powershell
cd apps/bi/backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
Copy-Item .env.example .env
uvicorn bi.api.main:app --host 127.0.0.1 --port 8000 --workers 1 --no-access-log --no-proxy-headers
```

En otra terminal:

```powershell
cd apps/bi/frontend
Copy-Item .env.example .env.local
pnpm install --frozen-lockfile
pnpm dev
```

Abrir `http://localhost:3000/bi`. Backend: `http://127.0.0.1:8000/api/v1/health`; documentación y contrato: `/api/v1/docs` y `/api/v1/openapi.json`. Si cambia el origen del frontend, ajustar `FRONTEND_ORIGIN`/`CORS_ORIGINS`. `NEXT_PUBLIC_API_BASE_URL` se incorpora al build frontend.

## Flujo de uso y demos

Cargar archivo propio → seleccionar rubro → confirmar mapping → revisar validación/calidad → elegir y confirmar limpieza → dashboard → filtros → exportar. Las acciones destructivas requieren confirmación; las transformaciones quedan registradas. “Probar demo” usa el mismo pipeline real y muestra que los datos son sintéticos. Las demos no sustituyen el procesamiento del archivo propio.

CSV y XLSX son los únicos formatos aceptados. XLSX permite cambiar hoja mientras está en etapa parsed; después de confirmar mapping se elimina el source. Se rechazan macros, vínculos externos, OLE, archivos corruptos y ZIP excesivos. Las fórmulas de entrada se leen como valores almacenados, nunca se ejecutan. La configuración de parsing decimal/miles/fechas pertenece a SourceSettings; el formato de pantalla utiliza Intl es-AR y la moneda informada por backend. Monedas mixtas bloquean métricas monetarias hasta seleccionar una moneda; no hay FX.

## Límites y privacidad temporal

Defaults configurables en `.env.example`: 20 MB, 250.000 filas, 200 columnas, preview 50 (máximo 100), profiling 20.000, 2 operaciones pesadas simultáneas, 10 intentos de creación/hora/IP, 100 sesiones globales y 10 por IP. CSV/XLSX sobre límite se rechazan, sin truncamiento. Solo preview/profiling usan muestra; validación, métricas y exports usan todas las filas.

TTL: 60 minutos por inactividad y máximo absoluto 240 minutos. Reaper al iniciar y cada 120 segundos. CSV source se borra al parsear; XLSX source al confirmar mapping. Raw permanece inmutable; canonical se reconstruye desde raw/configuración/mapping/acciones. TTL/DELETE eliminan todos los archivos de la sesión. “Terminar y borrar mis datos” está disponible durante el flujo; no se guarda contenido en localStorage. Las URLs de sesión son capacidades temporales: no compartirlas. Ver [deployment, seguridad y privacidad](docs/deployment_mvp.md).

## Exports

CSV UTF-8 con BOM y formato regional; XLSX con Datos, Registro de cambios y Resumen. Permite datos limpios o filtrados, encabezados amigables/originales y columnas originales/ignoradas. La exportación mantiene los filtros del dashboard mostrado. Se neutralizan fórmulas en texto sin alterar números negativos.

## Verificación

Desde backend activado:

```powershell
pytest
lint-imports --config importlinter.ini
python -m pip check
```

Desde frontend, con backend local en puerto 8000:

```powershell
pnpm generate:api-types
pnpm lint
pnpm typecheck
pnpm test
pnpm build
pnpm install:e2e
pnpm test:e2e
```

Playwright levanta backend en 8100 y frontend en 3100, un worker, sin sleeps de UI; verifica archivos propios de las tres industrias, demos, axe, teclado, filtros, tablas, responsive, CSV/XLSX y DELETE. Para un Python distinto usar `E2E_PYTHON` con su ruta. En Windows se puede reutilizar Edge: `$env:PLAYWRIGHT_CHANNEL='msedge'`. En CI se instala Chromium. Para verificar el build de producción, ejecutar primero `NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8100 pnpm build` (en PowerShell: `$env:NEXT_PUBLIC_API_BASE_URL='http://127.0.0.1:8100'; pnpm build`) y después `$env:E2E_PRODUCTION='true'; pnpm test:e2e`. Los traces/screenshots quedan únicamente en fallos; no contienen archivos reales de clientes. La suite genera los datasets moderados en runtime. CI usa instalación frozen, tests, lint/typecheck/build, import-linter y un job E2E independiente.

## Troubleshooting

- Error de CORS: usar exactamente el origen configurado, incluido puerto y localhost/127.0.0.1.
- Sesión vencida/no encontrada: cargar nuevamente; no se recupera contenido borrado.
- 429: esperar la ventana de rate limit o borrar una sesión para liberar cupo.
- XLSX rechazado: revisar formato real, contenido activo, ZIP y límites; no renombrar formatos incompatibles.
- Validación bloqueante: revisar mapping y datos; no se descartan filas inválidas silenciosamente.
- Playwright: cerrar procesos anteriores que ocupen 8100/3100, instalar Chromium o seleccionar un canal instalado.
- Permisos/disco: usar una carpeta temporal exclusiva, escribible y con espacio; revisar el request_id en logs seguros.

[Documento de cierre técnico](docs/fase8_hardening.md). No hay autenticación, base de datos, colas ni almacenamiento cloud.
