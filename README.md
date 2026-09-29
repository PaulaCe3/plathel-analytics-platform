# Data Analytics Platform

Monorepo mínimo para un ecosistema de ocho herramientas de analítica. La primera aplicación es **BI Multi-Industria** y está separada en un backend FastAPI y un frontend Next.js.

El estado actual es **Fase 0 — Esqueleto**. Incluye infraestructura, salud del sistema, metadatos de configuración, manejo de errores, observabilidad básica, contrato OpenAPI y generación de tipos TypeScript. Todavía no procesa archivos ni construye dashboards.

## Arquitectura

- `analytics_core`: capacidades generales reutilizables por las futuras aplicaciones. No puede importar `bi`.
- `bi`: API, servicios y futuras capacidades exclusivas del producto BI.
- La API es delgada: los routers delegan en servicios.
- FastAPI OpenAPI es la fuente de verdad de los tipos del frontend.
- No se usan base de datos, ORM, colas, microservicios ni herramientas de monorepo.

```text
data-analytics-platform/
├── .github/workflows/ci.yml
├── apps/bi/
│   ├── backend/
│   │   ├── src/analytics_core/
│   │   ├── src/bi/
│   │   └── tests/
│   └── frontend/
│       └── src/
├── docs/
├── .gitignore
└── README.md
```

## Requisitos

- Python 3.12 o superior
- Node.js 20.9 o superior
- pnpm 11 recomendado; los scripts de `package.json` también pueden ejecutarse con npm

## Backend

Desde `apps/bi/backend`:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
Copy-Item .env.example .env
uvicorn bi.api.main:app --reload --port 8000
```

Servicios disponibles:

- `GET http://127.0.0.1:8000/api/v1/health`
- `GET http://127.0.0.1:8000/api/v1/meta`
- OpenAPI: `http://127.0.0.1:8000/api/v1/openapi.json`
- Swagger UI: `http://127.0.0.1:8000/api/v1/docs`

## Frontend

Desde `apps/bi/frontend`, con el backend iniciado:

```powershell
Copy-Item .env.example .env.local
pnpm install
pnpm generate:api-types
pnpm dev
```

Abrir `http://localhost:3000/bi`. La pantalla consulta el backend mediante el cliente centralizado de `src/lib/api`.

## Verificaciones

Backend, desde `apps/bi/backend`:

```powershell
pytest
lint-imports --config importlinter.ini
```

Frontend, desde `apps/bi/frontend`:

```powershell
pnpm lint
pnpm typecheck
pnpm build
```

Regenerar los tipos TypeScript cuando cambie el contrato OpenAPI:

```powershell
pnpm generate:api-types
```

El comando requiere el backend disponible en `http://127.0.0.1:8000`.

## Alcance actual

La Fase 0 no incluye carga o lectura de archivos, sesiones de datasets, perfiles de industria, mapeo, calidad, limpieza, modelo canónico, métricas, `QuerySpec`, gráficos, dashboard, insights ni exportación.
