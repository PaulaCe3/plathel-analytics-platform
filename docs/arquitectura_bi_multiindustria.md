# Arquitectura — BI Multi-industria (app 1 de 8)

**Versión 1.0 · Documento de diseño para implementación**
Audiencia: quien implemente el proyecto (ChatGPT u otro). Este documento define *qué construir y dónde vive cada cosa*. No contiene la implementación completa; los bloques de código son **contratos** (firmas, modelos), no lógica.

---

## 0. Mapa del documento

| Bloque | Secciones |
|---|---|
| Decisiones y estructura | 1 Decisiones clave · 2 Repositorio · 3 Estructura y dependencias |
| Dominio de datos | 4 Modelo canónico · 5 Perfiles de industria · 6 Ingesta · 7 Mapeo · 8 Validación, calidad, limpieza, auditoría · 9 Motor de datos |
| Producto BI | 10 Métricas · 11 Comparaciones · 12 Filtros · 13 Dashboard · 14 Insights · 15 Exportación, demo, interoperabilidad |
| Contrato | 16 API · 17 Schemas y ejemplos JSON |
| Transversales | 18 Frontend · 19 Seguridad y privacidad · 20 Archivos grandes · 21 Errores, i18n, regional · 22 Responsive y accesibilidad · 23 Testing · 24 Observabilidad |
| Ejecución | 25 Roadmap · 26 Supuestos, riesgos, fuera de alcance · 27 Reglas para el implementador |

---

## 1. Decisiones clave (y por qué)

| # | Decisión | Razón |
|---|---|---|
| D1 | **Todo cálculo es una `QuerySpec` declarativa** que ejecuta un `DataEngine`. KPIs, gráficos, tablas e insights usan el mismo mecanismo. | Es el único punto donde se aplican filtros (consistencia garantizada) y el único punto que hay que reescribir para pasar a Polars/DuckDB. |
| D2 | **Dos paquetes Python:** `analytics_core` (preparación de datos, reutilizable por las 8 apps) y `bi` (producto BI). | Las 8 apps necesitan ingesta → mapeo → limpieza; ninguna necesita el dashboard de BI. Es solo una frontera de carpetas hoy, no un servicio. |
| D3 | **Perfil de industria = objeto Python tipado (Pydantic)** con dos secciones: `data` (modelo de datos, alias, terminología) y `bi` (métricas, dashboard, insights). | Tipado, validable en tests, sin mini-lenguajes en YAML. La sección `bi` es opcional: otras apps agregarán `rfm`, `forecast`, etc. sin tocar `data`. |
| D4 | **Modelo canónico en 3 capas:** universal → extensión de perfil → custom. | Ningún campo es obligatorio en el core; la obligatoriedad la decide cada perfil. |
| D5 | **Pandas confinado** en `analytics_core/engine/pandas_impl/`. Nadie más lo importa (se verifica con `import-linter`). | Requisito explícito de poder cambiar de motor. |
| D6 | **El backend calcula todo; el frontend solo renderiza.** El backend devuelve gráficos en formato *neutral* (series, categorías, formato), no opciones de ECharts. | Testeabilidad de métricas y libertad de cambiar la librería de gráficos. |
| D7 | **Sesión temporal de dataset en disco (Parquet) con TTL. Sin base de datos.** | Cumple “no persistir”, evita reparsear en cada request, memoria acotada. |
| D8 | **Pipeline determinista:** `canonical = f(raw, source_settings, mapping, acciones_de_limpieza)`. | Permite “reiniciar a original”, reproducibilidad y un log de auditoría simple. |
| D9 | **Nada silencioso.** Se distingue *hallazgo* (detectar) de *transformación* (cambiar). Toda transformación queda en un log append-only. | Regla fundamental del brief. |
| D10 | **Métricas imposibles: no se muestran en el cuerpo del dashboard**, pero se listan en un panel “No disponibles” con el campo faltante y un enlace al mapeo. Además, el paso de mapeo muestra en vivo “con este mapeo se habilitan N métricas”. | Dashboard limpio sin ocultar el porqué. Detalle en §10.4. |
| D11 | **Dashboard dirigido por configuración *moderada*:** la config decide *qué y dónde*; el código decide *cómo*. | Equilibrio flexibilidad/simplicidad. Detalle en §13.3. |
| D12 | **Monorepo mínimo** (sin Turborepo/Nx) con la primera app bajo `apps/bi`. | Costo casi cero hoy; evita migrar repos después. Detalle en §2. |
| D13 | **Todo síncrono en el MVP**, pero las respuestas incluyen `status`/`stage` para admitir jobs asíncronos luego. | Sin colas ni workers ahora; sin romper el contrato después. |
| D14 | **Contrato = OpenAPI de FastAPI → tipos TypeScript generados** (`openapi-typescript`). | Elimina el “shared/” manual y la deriva entre front y back. |

---

## 2. Repositorio: ¿A (repo BI) o B (monorepo)?

| | A — Repo independiente | B — Monorepo |
|---|---|---|
| Ventajas | Máxima simplicidad inicial | Reutilizar `analytics_core` y UI sin publicar paquetes; un CI; historia unificada; una sola web de la empresa |
| Desventajas | Al llegar la app 2 hay que copiar código o publicar paquetes; se fragmentan issues/CI | Riesgo de sobreingeniería si se usan herramientas pesadas |

**Recomendación: B, en versión mínima.**
- Un repositorio, carpeta `apps/bi/` con `frontend/` y `backend/`.
- **Sin** herramientas de monorepo (Nx/Turborepo/Bazel). Carpetas y dos CI jobs alcanzan.
- `analytics_core` vive hoy dentro de `apps/bi/backend/src/` con la frontera protegida por `import-linter`. **Regla de promoción:** al empezar la app 2, se mueve a `packages/analytics_core/` (un `git mv` + dependencia por path). No antes.
- Lo mismo con UI compartida: recién cuando exista la app 2, se extrae `packages/ui`.
- **App 2 implementada:** forecasting temporal en `apps/forecast/backend/src/forecast`; core promovido a `packages/analytics_core/src/analytics_core` y UI a `packages/ui`. El shell Next existente sirve `/bi` y `/forecast`; `platform_api` compone routers sin dependencias entre productos.

---

## 3. Estructura y reglas de dependencia

### 3.1 Árbol del repositorio

```
data-analytics-platform/
├─ apps/
│  └─ bi/
│     ├─ backend/
│     │  ├─ pyproject.toml
│     │  ├─ importlinter.ini
│     │  ├─ src/
│     │  │  ├─ analytics_core/          # reutilizable (sin BI, sin rubros)
│     │  │  └─ bi/                      # producto BI
│     │  ├─ demo_data/                  # datasets demo (§15.2)
│     │  └─ tests/
│     └─ frontend/
├─ docs/                                # este documento, ADRs
└─ README.md
```

### 3.2 Backend

```
src/analytics_core/
├─ canonical/
│  ├─ fields.py            # FieldSpec + catálogo de campos universales
│  ├─ derived.py           # DerivedFieldRule (ej. amount = unit_price × quantity)
│  └─ manifest.py          # CanonicalManifest versionado (interoperabilidad, §15.3)
├─ engine/
│  ├─ base.py              # Protocol DataEngine + EngineTable (handle opaco)
│  ├─ query.py             # QuerySpec, MeasureSpec, GroupBy, FilterClause, QueryResult
│  ├─ factory.py           # get_engine() según settings
│  └─ pandas_impl/         # ÚNICO lugar con `import pandas`
│     ├─ engine.py
│     ├─ readers.py        # lectura CSV/XLSX a texto
│     ├─ parsers.py        # números, fechas, monedas
│     ├─ checks.py         # ejecución de checks de calidad
│     └─ transforms.py     # ejecución de acciones de limpieza
├─ sources/
│  ├─ base.py              # Protocol SourceConnector (fetch() -> RawTable)
│  ├─ upload.py            # UploadSource
│  └─ demo.py              # DemoSource
├─ ingestion/
│  ├─ sniffing.py          # encoding, delimitador, hoja, fila de encabezado (sin pandas)
│  ├─ locale_inference.py  # decimal/miles/fecha por muestra
│  └─ headers.py           # normalización y deduplicación de encabezados
├─ mapping/
│  ├─ matcher.py           # sugerencias (alias + fuzzy + contenido)
│  ├─ compatibility.py     # tipo de columna vs tipo de campo
│  └─ models.py            # ColumnMapping, ColumnDisposition
├─ validation/             # reglas bloqueantes/avisos sobre mapeo y tipos
├─ quality/                # catálogo de checks + score
├─ cleaning/
│  ├─ actions.py           # catálogo declarativo de CleaningAction
│  ├─ planner.py           # arma el plan con impacto estimado
│  └─ recorder.py          # TransformationRecorder (log de auditoría)
├─ exports/
│  ├─ base.py              # Protocol Exporter + registry
│  ├─ csv_exporter.py
│  └─ xlsx_exporter.py
├─ sessions/
│  ├─ store.py             # DatasetSessionStore (disco temporal)
│  └─ reaper.py            # limpieza por TTL
├─ security/
│  ├─ upload_guard.py      # validación de archivos
│  ├─ sanitize.py          # nombres, celdas de export
│  └─ rate_limit.py
├─ errors.py               # jerarquía AppError + códigos
├─ i18n.py                 # translate(key, locale, **params) + TermResolver
├─ logging.py              # logging JSON + request_id + timed()
└─ settings.py             # límites y configuración (pydantic-settings)

src/bi/
├─ profiles/
│  ├─ base.py              # IndustryProfile, ProfileData, BIConfig
│  ├─ registry.py          # register_profile(), get_profile()
│  ├─ custom/              # perfil genérico (base de todo)
│  ├─ retail_ecommerce/
│  ├─ services/
│  ├─ hospitality/
│  └─ …                    # saas, real_estate, tourism, gastronomy, distribution, education
│     # cada carpeta: profile.py, metrics.py (opcional), insights.py (opcional), labels_es.py
├─ metrics/
│  ├─ expr.py              # Expr: Sum, CountDistinct, Ratio, Sub, RowMul, …
│  ├─ definition.py        # MetricDefinition
│  ├─ registry.py          # register_metric(), catálogo
│  ├─ universal.py         # métricas universales
│  ├─ availability.py      # resolve_availability(profile, mapping)
│  └─ comparison.py        # ComparisonResolver
├─ insights/
│  ├─ engine.py            # ejecuta reglas, prioriza, deduplica
│  ├─ config.py            # umbrales
│  └─ rules/universal.py
├─ dashboard/
│  ├─ templates.py         # DashboardTemplate + secciones estándar
│  ├─ builder.py           # DashboardBuilder.build(...) → DashboardSpec
│  ├─ widgets.py           # resolución widget → QuerySpec → WidgetResult
│  └─ filters.py           # derivación de FilterDefinition
├─ services/               # orquestación (sin HTTP)
│  ├─ dataset_service.py
│  ├─ prepare_service.py   # mapping → canonical → validate → quality → plan
│  └─ dashboard_service.py
└─ api/
   ├─ main.py              # app factory, CORS, handlers de error
   ├─ middleware.py        # request_id, timing, límites
   ├─ deps.py
   ├─ routers/             # meta, profiles, datasets, mapping, cleaning, dashboard, export, demo
   └─ schemas/             # modelos request/response de la API

tests/
├─ unit/ · integration/ · contract/ · fixtures/
```

### 3.3 Reglas de dependencia (se verifican con `import-linter`)

1. `analytics_core` **no importa** `bi`.
2. `import pandas` (y `numpy`) **solo** dentro de `analytics_core/engine/pandas_impl/`.
3. `bi.profiles` **no importa** `bi.api` ni `bi.dashboard`.
4. `bi.api` solo llama a `bi.services`; los routers no contienen lógica.
5. Ningún módulo de `analytics_core` ni de `bi/{metrics,dashboard,insights}` contiene literales de industria (`"retail"`, `"hotel"`…). Un test lo verifica (§23.4).

### 3.4 Frontend (resumen; detalle en §18)

```
frontend/src/
├─ app/bi/…                  # rutas
├─ features/                 # industry-select, upload, column-mapper, data-review, dashboard, export
├─ components/{ui,charts,data-display}/
├─ lib/{api,format,i18n}/
├─ hooks/  ·  types/ (generados)
```

---

## 4. Modelo canónico

### 4.1 Tres capas

| Capa | Qué es | Dónde se define |
|---|---|---|
| **Universal** | Conceptos que existen en casi cualquier negocio (fecha, importe, cliente, concepto…). Ninguno es obligatorio por sí mismo. | `analytics_core/canonical/fields.py` |
| **Extensión de perfil** | Campos propios de un rubro (`check_in`, `nights`, `plan`, `duration_hours`…). | En el `profile.py` del rubro |
| **Custom** | Columnas del cliente que el sistema no conoce. Se conservan y pueden promoverse a dimensión o medida. | Definidas por el usuario en el mapeo |

**Regla de obligatoriedad:** el core solo exige que exista **al menos una medida** para construir un dashboard. Cada perfil declara qué campos son `required`, `recommended` u `optional`.

### 4.2 Campos universales

| id | kind | dtype | Significado |
|---|---|---|---|
| `date` | time | date/datetime | Fecha principal de análisis |
| `transaction_id` | identifier | string | Identificador de operación (pedido, ticket, reserva, factura) |
| `customer_id` | identifier | string | Identificador de cliente |
| `customer_name` | dimension | string | Nombre de cliente |
| `concept` | dimension | string | **Qué** se vendió: producto, servicio, habitación, curso… |
| `category` | dimension | string | Agrupación del concepto |
| `subcategory` | dimension | string | Subagrupación |
| `amount` | measure | decimal | Valor monetario **total** de la fila |
| `quantity` | measure | decimal | Cantidad |
| `unit_price` | measure | decimal | Precio unitario |
| `cost` | measure | decimal | Costo **total** de la fila |
| `discount` | measure | decimal | Descuento en valor monetario |
| `channel` | dimension | string | Canal de venta/captación |
| `location` | dimension | string | Ubicación (sucursal, provincia, zona) |
| `responsible` | dimension | string | Vendedor, profesional, agente… |
| `status` | dimension | string | Estado de la operación |
| `currency` | dimension | string | Moneda por fila (informativo en MVP, §21.3) |

### 4.3 Campos de extensión

Cada perfil declara los suyos como `FieldSpec` (`scope="extension"`). **Política de colisión:** un mismo `id` en dos perfiles debe tener definición idéntica (lo verifica un test). Así, agregar una industria no exige editar ningún archivo central.

Ejemplos: Hotelería → `check_in`, `check_out`, `nights`, `room_type`, `guests`, `booking_date`. Servicios → `duration_hours`, `project`. SaaS → `plan`, `start_date`, `end_date`, `billing_period`.

### 4.4 Campos derivados

Un perfil (o el core) puede declarar reglas para **calcular** un campo cuando falta:

| Regla | Condición | Nota |
|---|---|---|
| `amount = unit_price × quantity` | `amount` sin mapear, existen ambos | Universal |
| `nights = check_out − check_in` | `nights` sin mapear | Hotelería |
| `amount = rate × nights` | `amount` sin mapear | Hotelería |

Toda derivación se registra en el log de transformaciones (“Se calculó Importe = Precio × Cantidad”) y es visible en el mapeo (“Importe: calculado”).

### 4.5 Columnas fuera del modelo: estados (`ColumnDisposition`)

**Ninguna columna se elimina automáticamente.** Cada columna del archivo tiene exactamente un estado:

| Estado | Efecto |
|---|---|
| `canonical` | Mapeada a un campo (universal o de extensión) |
| `custom_dimension` | Disponible como filtro y desglose (`custom__<slug>`) |
| `custom_measure` | Numérica, disponible para sumas/promedios |
| `ignored` | Excluida del análisis; **conservada** y exportable con “incluir columnas originales” |

**Sugerencia automática para columnas sin mapear:** texto con cardinalidad 2–50 y ≥ 80 % completo → sugerir `custom_dimension`; numérica → sugerir `custom_measure`; texto de alta cardinalidad o casi único → sugerir `ignored`. Siempre sugerido, nunca aplicado sin confirmación en pantalla (la casilla viene marcada y se puede cambiar).

**Límites:** máx. 10 dimensiones custom y 5 medidas custom por dataset (configurable); el desglose usa top-N + “Otros”.

### 4.6 Grano de fila y transacciones

Una fila puede ser una línea de pedido o la operación completa. Regla: `transactions = COUNT DISTINCT transaction_id` si está mapeado; si no, se cuenta cada fila como una transacción y se emite el warning *“Cada fila se cuenta como una transacción porque no hay identificador”*.

### 4.7 Opciones de mapeo (`ColumnMapping.options`)

Algunas columnas son ambiguas semánticamente. El mapeo puede llevar opciones que **normalizan al concepto canónico** al construir el dataset:

| Campo | Opción | Efecto |
|---|---|---|
| `cost` | `basis: "unit" \| "total"` | Si `unit`, se multiplica por `quantity` (requiere `quantity`) |
| `discount` | `kind: "amount" \| "percent"` | Si `percent`, se convierte a monto con `amount` |
| `amount` | `basis: "total" \| "unit"` | Si `unit`, se multiplica por `quantity` |

---

## 5. Perfiles de industria

### 5.1 Modelo

```python
class IndustryProfile(BaseModel):
    id: str                          # "hospitality"
    version: str                     # "1.0"
    name: LocalizedText              # {"es": "Hotelería", "en": "Hospitality"}
    description: LocalizedText
    icon: str
    data: ProfileData
    bi: BIConfig | None = None       # otras apps agregarán rfm=..., forecast=...

class ProfileData(BaseModel):
    fields: list[ProfileFieldRule]           # (field, level: required|recommended|optional)
    extension_fields: list[FieldSpec]        # campos propios del rubro
    aliases: dict[str, list[str]]            # field_id -> alias de encabezados
    derived: list[DerivedFieldRule]
    checks: list[ProfileCheck]               # validaciones extra (ej. check_out > check_in)
    terminology: dict[Locale, dict[str, str]]# {"es": {"concept": "Habitación", "amount": "Ingreso"}}
    parameters: list[ProfileParameter]       # datos que el archivo no trae (ej. total_rooms)
    primary_date: str = "date"               # hotelería: "check_in"
    alternate_dates: list[str] = []          # hotelería: ["booking_date"]

class BIConfig(BaseModel):
    metrics: list[str]                # ids del registry (universales + propias)
    kpi_order: list[str]
    featured_dimensions: list[str]    # ej. ["category","channel","location"]
    dashboard: DashboardTemplate      # secciones y widgets declarativos
    insight_rules: list[str]
    extra_filters: list[str] = []
```

**Parámetros de perfil** (`ProfileParameter`): valores opcionales que el usuario ingresa en la UI cuando una métrica los necesita. Ejemplo: `total_rooms` habilita **Ocupación**. Sin parámetro, la métrica queda en “No disponibles” indicando qué falta.

**Fecha principal alternativa:** el usuario puede cambiar la base temporal (“Analizar por: check-in / fecha de reserva”). Es un parámetro del request del dashboard (`time_field`), no un perfil distinto.

### 5.2 Terminología sin duplicar lógica

Orden de resolución de cualquier texto visible:

`profile.data.terminology[locale][key]` → catálogo del core `messages/<locale>.json` → la propia clave.

Las plantillas usan marcadores: `"{concept} principal: {value}"`. Retail muestra “Producto principal”, Hotelería “Habitación principal”. La lógica (métricas, insights, widgets) es una sola. Lo resuelve `TermResolver` en `analytics_core/i18n.py`.

### 5.3 Catálogo de perfiles

| Perfil | `concept` | `responsible` | `amount` | Extensión típica | Métricas específicas | Fase |
|---|---|---|---|---|---|---|
| **custom** (genérico) | Concepto | Responsable | Importe | — | solo universales | **MVP** |
| **retail_ecommerce** | Producto | Vendedor | Venta | — | unidades, margen bruto, % margen, descuento medio | **MVP** |
| **services** | Servicio | Profesional | Facturación | `duration_hours`, `project` | horas facturadas, ingreso por hora | **MVP** |
| **hospitality** | Habitación | Recepcionista / canal | Ingreso | `check_in`, `check_out`, `nights`, `room_type`, `guests`, `booking_date` | noches, ADR, estadía media, ocupación (con `total_rooms`) | **MVP** |
| saas | Plan | Ejecutivo | Ingreso | `plan`, `start_date`, `end_date`, `billing_period` | MRR, ARR, suscripciones activas | V1.1 (necesita `IntervalExpr`, §10.6) |
| real_estate | Propiedad | Agente | Valor de operación | `operation_type`, `property_type` | precio medio, operaciones por agente/zona | V1.1 |
| tourism | Excursión | Operador | Ingreso | `destination`, `passengers` | pasajeros, ingreso por pasajero | V1.1 |
| gastronomy | Producto | Mozo/Cajero | Venta | `table`, `payment_method` | ticket medio, propina si existe | V1.1 |
| distribution | Producto | Vendedor | Importe | `zone` | unidades, cobertura de clientes | V1.1 |
| education | Curso | Asesor | Ingreso | `program`, `campus`, `modality`, `student_id` | inscripciones, ingreso por programa | V1.1 |

> **Recomendación de orden:** implementar `custom` primero. Es la línea base que prueba que el core no depende de ningún rubro; los demás son configuración encima.

### 5.4 Agregar una industria (checklist objetivo)

Debe implicar **solo**: (1) carpeta nueva `profiles/<id>/` con `profile.py`; (2) métricas propias si las hay, registradas en su `metrics.py`; (3) alias; (4) widgets en su `DashboardTemplate`; (5) fixtures y tests. **Cero** cambios en `analytics_core`, `bi/api`, `bi/metrics/{expr,registry,availability}`, `bi/dashboard/{builder,widgets}`. Si algo de esto es necesario, es señal de acoplamiento y debe corregirse en el core.

### 5.5 Registro y validación de perfiles

`registry.py` descubre los perfiles al arrancar (importando `profiles/*/profile.py`). Un test de contrato recorre **todos** los perfiles y verifica: métricas referenciadas existen; campos referenciados existen (universales o de la propia extensión); alias sin colisiones dentro del perfil; `primary_date` es un campo `time`; todo `required` figura en `fields`; todo texto tiene clave de `terminology` o de catálogo en `es`.

---

## 6. Ingesta

### 6.1 Principio central

**Leer todo como texto y parsear en una etapa controlada.** Así se pueden contar y reportar errores por columna en lugar de que el lector “adivine” tipos y falle o corrompa datos. El resultado del primer paso es una tabla `raw` de strings, guardada como Parquet.

### 6.2 CSV

| Aspecto | Estrategia |
|---|---|
| Encoding | `charset-normalizer` sobre los primeros ~64 KB; orden de preferencia: UTF-8 (con/sin BOM) → cp1252 → latin-1. Si la confianza es baja, se informa y el usuario puede elegir en `SourceSettings`. |
| Delimitador | `csv.Sniffer` con fallback por conteo consistente de `, ; \t \|` en las primeras N líneas |
| Comillas / saltos de línea en celdas | Manejados por el parser CSV, no por `split` |
| Filas vacías / columnas vacías | Se cuentan y reportan; no se eliminan hasta que el usuario lo acepte (§8) |
| Líneas malformadas | Se reportan con número de línea; opción “omitir líneas inválidas” es una acción de limpieza, no un default |

### 6.3 Excel (XLSX)

- `openpyxl` con `read_only=True, data_only=True` (valores, nunca fórmulas evaluadas por nosotros).
- **Múltiples hojas:** el upload devuelve la lista de hojas y parsea por defecto la primera con datos; el usuario cambia de hoja vía `PATCH /datasets/{id}` y se reparsea. En el MVP se analiza **una hoja a la vez** (no se unen hojas).
- **Fila de encabezado:** autodetección (primera fila con ≥ 60 % de celdas de texto no vacías y seguida de filas de datos); el usuario puede fijar `header_row`.
- Celdas combinadas, filas de título sobre la tabla y filas de totales al final: se detectan y se avisan (no se corrigen solos).
- Fechas de Excel (seriales y `datetime`) se normalizan a texto ISO en `raw`.
- Formatos rechazados en el MVP: `.xls`, `.xlsm`, `.xlsb`, `.ods` (mensaje amigable indicando “guardar como .xlsx”).

### 6.4 Encabezados

- Se normalizan espacios, BOM y saltos de línea; encabezados vacíos → `columna_N`; duplicados → sufijo `_2`, `_3`.
- Cada columna tiene una **`key` estable** (`c01`, `c02`…) más `original_name`. **El mapeo referencia siempre la `key`**, no el nombre (evita ambigüedades con duplicados).

### 6.5 Configuración regional de *lectura* (`SourceSettings`)

Se **infiere** y se puede **corregir** por el usuario (globalmente o por columna):

| Ajuste | Inferencia |
|---|---|
| Separador decimal / de miles | Patrones por columna sobre la muestra: `1.234,56`, `1,234.56`, `1234.56`. Si el patrón es ambiguo (`1,234`) se pregunta; jamás se asume en silencio. |
| Símbolos de moneda, `%`, espacios, negativos entre paréntesis `(100)`, signo final `100-` | Se limpian al parsear numéricos y se informa la cantidad afectada |
| Formato de fecha | Lista de formatos candidatos por columna. **Ambigüedad día/mes:** si algún valor tiene primer componente > 12 → día primero; si todos ≤ 12 → se usa la preferencia del locale (`es-AR`: día primero) y se emite warning con opción de invertir. Soporta fecha+hora, serial de Excel y años de 2 dígitos. |
| Fechas con formatos mezclados | Se parsea lo posible y se reporta el resto como “formatos inconsistentes” (con conteo) |

### 6.6 Preparación para conectores futuros

```python
class SourceConnector(Protocol):
    kind: str                                  # "upload" | "demo" | "google_sheets" | "sql" | …
    def fetch(self) -> RawTable: ...           # devuelve tabla de texto + metadatos de origen
```

MVP: `UploadSource` y `DemoSource`. Todo lo posterior a `fetch()` (mapeo, calidad, dashboard) **no sabe de dónde vino el dato**. Google Sheets, SQL, Shopify, etc. serán nuevas implementaciones sin tocar el resto (con autenticación, que hoy queda fuera).

---

## 7. Mapeo de columnas

### 7.1 Algoritmo de sugerencia (`mapping/matcher.py`)

Para cada par (columna del archivo, campo del perfil) se calcula un puntaje 0–1:

| Señal | Peso | Detalle |
|---|---|---|
| Alias exacto normalizado | 0.50 | Normalización: minúsculas, sin acentos, sin signos, singular simple, tokens |
| Similitud difusa | hasta 0.25 | `rapidfuzz` (token_set_ratio) contra nombre y alias |
| Compatibilidad de contenido | hasta 0.20 | ¿≥ 90 % parseable como fecha/número? ¿ratio de unicidad alto → id? ¿cardinalidad baja → dimensión? |
| Posición/contexto | hasta 0.05 | Columnas adyacentes (ej. `check_in` seguida de `check_out`) |

Se asigna con una **resolución global** (un campo → una columna; una columna → un campo) maximizando el puntaje total, no columna por columna.

| Confianza | Rango | UI |
|---|---|---|
| Alta | ≥ 0.85 | Preseleccionado, marcado “Sugerido” |
| Media | 0.60–0.85 | Preseleccionado con aviso “Revisar” |
| Baja | < 0.60 | Sin preseleccionar; se ofrecen las 3 mejores candidatas |

Cada sugerencia incluye `reasons` (“coincide con alias ‘valor_total’”, “el 98 % de los valores son números”) para que la UI pueda explicarla.

### 7.2 Detección de mapeos incompatibles

| Caso | Severidad |
|---|---|
| Campo `measure` con < 90 % de valores parseables como número | error (bloquea) |
| Campo `time` con < 90 % parseable como fecha | error (bloquea) |
| Dos columnas al mismo campo | error |
| Falta campo `required` del perfil | error (bloquea) |
| Falta campo `recommended` | warning (informa qué se pierde) |
| Columna casi sin datos (> 95 % vacía) mapeada a algo relevante | warning |
| `customer_id` con unicidad ≈ 100 % en una tabla con muchas filas (parece id de fila) | info |

### 7.3 UX del paso de mapeo

- Tabla: *campo del modelo* ↔ *columna del archivo* (selector), con vista previa de 5 valores y el tipo detectado.
- **Panel lateral “Con este mapeo se habilita…”**: lista en vivo de métricas y secciones que quedan disponibles o no (y por qué). Se calcula con `PUT /datasets/{id}/mapping` (es idempotente y barato).
- Columnas sin mapear: lista aparte con el estado sugerido (§4.5) editable.
- Campos derivados visibles como “calculado”.
- V1.1: guardar plantillas de mapeo **en `localStorage` del navegador** (clave por hash de encabezados). No se persiste nada en el servidor.

---

## 8. Validación, calidad, limpieza y auditoría

### 8.1 Tres conceptos, tres responsabilidades

| | Validación | Data Quality | Limpieza |
|---|---|---|---|
| Pregunta | ¿Se puede construir el dashboard? | ¿Cómo está el archivo? | ¿Qué cambio y cómo? |
| Salida | `ValidationReport` (bloquea o no) | `DataQualityReport` (descriptivo + score) | `CleaningPlan` → `TransformationLog` |
| Modifica datos | No | No | Sí, solo con confirmación |
| Módulo | `validation/` | `quality/` | `cleaning/` |

`POST /datasets/{id}/validate` ejecuta una sola pasada y devuelve **los tres**: validación, calidad y el plan de limpieza sugerido (con impacto estimado por acción).

### 8.2 Catálogo de checks (`quality/`)

Cada check es declarativo: `id`, `scope` (columna/campo/dataset), `severity`, `applies_to` (kind/dtype), `suggested_action`.

| Check | Severidad por defecto | Acción sugerida |
|---|---|---|
| `missing_values` (por columna, con ratio) | info/warning según ratio | rellenar / excluir del cálculo |
| `empty_column` | info | marcar `ignored` |
| `duplicate_rows` | warning | eliminar duplicados exactos |
| `duplicate_ids` (solo si `transaction_id` debería ser único por el grano) | warning | — (revisión manual) |
| `invalid_dates` | error si supera umbral, si no warning | excluir filas del cálculo temporal |
| `invalid_numbers` | ídem | excluir filas del cálculo |
| `negative_amounts` / `negative_quantities` | warning (pueden ser devoluciones) | informar; no se corrige |
| `type_mismatch` (columna mixta texto/número) | warning | — |
| `inconsistent_formats` (fechas o números con varios patrones) | warning | estandarizar |
| `leading_trailing_spaces`, `inconsistent_case` | info | trim / normalizar texto |
| `suspicious_total_row` (última fila con “total” y suma ≈ resto) | warning | quitar fila (opt-in) |
| `mixed_currency` (más de un valor en `currency`) | warning | exigir filtro por moneda |
| Checks de perfil (`ProfileCheck`) | según perfil | ej. `check_out > check_in`; `nights` inconsistente |

Cada hallazgo es un `Issue` con conteo, ratio y **hasta 5 `sample_row_ids`** (ids de fila, no valores) para inspección.

### 8.3 Data Quality Score — recomendación

**Incluirlo en el MVP, simple y explicable.** Los datos ya se calculan; agrega valor de demostración. Condiciones:

- Se llama **“Calidad estructural del archivo”**, nunca “calidad de tus datos” ni “de tu empresa”.
- Fórmula transparente y **siempre visible el desglose**:
  `score = 100 − Σ min(tope_c, k_c × ratio_c × 100)` para 4 categorías: completitud (tope 35), validez (35), unicidad (15), consistencia (15). Se calcula solo sobre columnas mapeadas o relevantes.
- Se muestra una banda (*Buena / Aceptable / Revisar*) con el número como dato secundario, para evitar falsa precisión.
- Si no se logra explicar el número en la UI, se muestra solo la banda.

### 8.4 Limpieza: catálogo y flujo

**Catálogo declarativo** (`cleaning/actions.py`); cada acción define `id`, `params`, `destructive: bool`, `default_selected`, y las funciones `estimate_impact()` y `describe()`. La ejecución real está en `pandas_impl/transforms.py`.

| Acción | Destructiva | Preseleccionada |
|---|---|---|
| `trim_whitespace` | no | sí |
| `normalize_text_case` (opcional por columna) | no | no |
| `parse_dates` / `parse_numbers` (convierte a tipos canónicos) | no* | **obligatoria e informada** |
| `standardize_categories` (unificar variantes obvias) | no | no |
| `drop_empty_columns` | sí | no |
| `drop_exact_duplicates` | sí | no |
| `drop_rows` (ids concretos: fila de totales) | sí | no |
| `fill_missing` (constante o valor) | sí | no |

\* El parseo no borra datos, pero **sí se registra** (ver §8.5). Los valores que no se pueden parsear **no se eliminan**: la fila queda marcada.

**Flujo (nada silencioso):**
1. `POST /validate` → devuelve el plan con “Se eliminarían 52 filas duplicadas” (impacto real, no genérico).
2. El usuario marca/desmarca acciones.
3. `PUT /datasets/{id}/cleaning` con la **lista completa** de acciones elegidas (idempotente).
4. El backend **reconstruye** `canonical` desde `raw` aplicando mapeo + acciones en orden y devuelve el `TransformationLog` y el reporte de calidad actualizado.
5. “Volver al original” = enviar lista vacía.

### 8.5 Filas inválidas (política)

No se borran. Se mantiene una máscara interna por campo (`_valid__amount`, `_valid__date`). Cada métrica excluye las filas inválidas **para sus campos requeridos** y el resultado incluye `excluded_rows`. El dashboard muestra un aviso discreto: *“12 filas no se incluyeron porque la fecha no es válida”*.

### 8.6 Auditoría de transformaciones

Un único mecanismo: `TransformationRecorder`. Toda acción de limpieza **debe** devolver un `TransformationResult`; la clase base lo exige y registra (no se puede aplicar un cambio sin log).

```python
class Transformation(BaseModel):
    id: str; seq: int
    action_id: str                                      # "drop_exact_duplicates"
    kind: Literal["parse","normalize","derive","remove","fill"]
    columns: list[str]
    params: dict
    rows_before: int; rows_after: int; rows_affected: int
    summary: str                                        # localizado: "Columna «Precio» convertida a formato numérico"
    examples: list[dict] = []                           # ≤3 {before, after}; solo en sesión, nunca a logs
    automatic: bool                                     # True = parseo obligatorio informado; False = elegido por el usuario
    at: datetime
```

- El log es **append-only** dentro de la sesión (`meta.json`) y se reconstruye al reaplicar acciones.
- Los **hallazgos** (`Issue`) y las **transformaciones** viven en listas separadas: detectar ≠ cambiar.
- Disponible por `GET /datasets/{id}/transformations` y como hoja **“Registro de cambios”** en el XLSX exportado.

---

## 9. Motor de datos (`DataEngine`) y `QuerySpec`

### 9.1 Contrato del motor

El resto del sistema **nunca** ve un `DataFrame`: recibe `EngineTable` (handle opaco) y devuelve resultados como modelos Pydantic.

```python
class DataEngine(Protocol):
    def read_raw(self, path: Path, settings: SourceSettings) -> EngineTable: ...
    def column_profiles(self, t: EngineTable, sample: int) -> list[ColumnProfile]: ...
    def build_canonical(self, raw: EngineTable, mapping: MappingSpec,
                        settings: SourceSettings, derived: list[DerivedFieldRule]
                        ) -> tuple[EngineTable, ParseReport]: ...
    def run_checks(self, t: EngineTable, checks: list[Check]) -> list[Issue]: ...
    def apply_action(self, t: EngineTable, action: CleaningActionSpec
                     ) -> tuple[EngineTable, TransformationResult]: ...
    def run_query(self, t: EngineTable, q: QuerySpec) -> QueryResult: ...
    def distinct_values(self, t: EngineTable, field: str, q: str | None, limit: int) -> list[ValueCount]: ...
    def date_coverage(self, t: EngineTable, field: str) -> DateCoverage: ...
    def to_parquet(self, t: EngineTable, path: Path) -> None: ...
    def from_parquet(self, path: Path) -> EngineTable: ...
    def iter_export(self, t: EngineTable, spec: ExportSpec) -> Iterator[Row]: ...
```

Son ~11 métodos: ese es el precio de la sustitución. DuckDB implementaría `run_query` traduciendo `QuerySpec` a SQL; Polars a expresiones lazy. **Los métodos que hoy toman una lista declarativa (`checks`, `action`) son la clave para que la lógica de negocio no dependa de pandas.**

### 9.2 `QuerySpec`

```python
class QuerySpec(BaseModel):
    measures: list[MeasureSpec]          # alias + Expr (Sum, CountDistinct, Mean, Ratio, …)
    group_by: list[GroupBy] = []         # field + grain opcional (day|week|month|quarter|year)
    filters: list[FilterClause] = []     # field, op(in|not_in|between|gte|lte|contains), values
    order_by: list[OrderBy] = []
    limit: int | None = None
    others_bucket: bool = False          # agrupa el resto en "Otros" cuando hay limit
```

`QueryResult` = filas `dict[str, Any]` + `columns` + `row_count`. Sin tipos de pandas.

**Regla:** los filtros del usuario se inyectan **una sola vez** en `dashboard_service` a cada `QuerySpec`. Ningún widget, métrica o insight aplica filtros por su cuenta.

---

## 10. Motor de métricas

### 10.1 `MetricDefinition`

```python
class MetricDefinition(BaseModel):
    id: str                                   # "revenue"
    label_key: str; description_key: str      # i18n (y terminología del perfil)
    group: str                                # "ventas" | "volumen" | "clientes" | …
    expr: Expr                                # declarativa, ver 10.2
    output: OutputSpec                        # type: currency|number|integer|percent|duration; decimals
    industries: list[str] | None = None       # None = universal
    comparable: bool = True                   # admite variación contra período anterior
    additive: bool = True                     # se puede sumar entre grupos → permite "% del total"
    polarity: Literal["higher_is_better","lower_is_better","neutral"] = "higher_is_better"

    @property
    def requires(self) -> set[str]: ...       # se DERIVA recorriendo `expr` (no se declara a mano)
```

`requires` se calcula automáticamente desde la expresión (incluyendo métricas referenciadas), eliminando el error clásico de declarar campos requeridos que no coinciden con el cálculo real.

### 10.2 Expresiones (`Expr`)

Árbol pequeño y cerrado (sin DSL de texto):

`Field(id)` · `AnyOf(field_a, field_b)` (ej. cliente por id o por nombre) · `Sum(e)` · `Mean(e)` · `Count()` · `CountDistinct(e)` · `Min/Max` · `Ratio(num, den)` (división segura) · `Sub(a, b)` · `RowMul(a, b)` (multiplicación fila a fila) · `MetricRef(id)`.

Ejemplo (contrato ilustrativo):

```python
register_metric(MetricDefinition(
    id="gross_margin", group="rentabilidad", industries=["retail_ecommerce"],
    label_key="metric.gross_margin", description_key="metric.gross_margin.desc",
    expr=Sub(Sum(Field("amount")), Sum(Field("cost"))),
    output=OutputSpec(type="currency"), polarity="higher_is_better",
))
```

Agregar una métrica = **una definición registrada + un test**. Nada en frontend, API ni dashboard cambia (si un widget la usa, se agrega a la plantilla del perfil).

### 10.3 Catálogo

| Métrica | Expr | Universal |
|---|---|---|
| `revenue` | `Sum(amount)` | sí |
| `transactions` | `CountDistinct(transaction_id)` (fallback: `Count()` con warning) | sí |
| `customers` | `CountDistinct(AnyOf(customer_id, customer_name))` | sí |
| `avg_transaction_value` | `Ratio(revenue, transactions)` | sí |
| `quantity` | `Sum(quantity)` | sí |
| `avg_unit_price` | `Ratio(revenue, quantity)` | sí |
| `revenue_share` | participación % (calculada en servicio con `additive`) | sí |
| `top_n_concentration` | participación de los N mayores de una dimensión | sí |
| `growth_vs_previous` | derivada de comparación (§11) | sí |
| Retail: `units_sold`, `gross_margin`, `margin_pct`, `avg_discount` | según definición | perfil |
| Servicios: `billed_hours`, `revenue_per_hour` | `Sum(duration_hours)`, `Ratio(revenue, billed_hours)` | perfil |
| Hotelería: `nights`, `adr`, `avg_stay`, `occupancy` | `Sum(nights)`, `Ratio(revenue, nights)`, `Ratio(nights, reservas)`, ver 10.6 | perfil |

### 10.4 Disponibilidad y estrategia UX (recomendación)

`resolve_availability(profile, mapping) → dict[metric_id, Available | Unavailable(missing=[fields])]`.

**Estrategia recomendada (híbrida):**

1. **Dentro del dashboard, las métricas no calculables NO se muestran** (ni tarjetas grises ni huecos): un dashboard con tarjetas vacías transmite “roto”.
2. Existe un panel plegable **“Métricas no disponibles (N)”** con cada métrica y qué campo falta: *“Margen bruto necesita: Costo”*, con enlace “Agregar columna en el mapeo”.
3. En el **paso de mapeo** se muestra en vivo cuántas métricas se habilitan y cuáles se desbloquean al mapear un campo faltante (“Mapeando ‘Costo’ se habilita Margen bruto”). Es el momento en que el usuario puede actuar.

Por qué esta y no las alternativas: solo ocultar deja al usuario sin saber por qué falta algo; deshabilitar en el dashboard ensucia la vista; informar solo en el dashboard llega tarde.

### 10.5 Resultado de métrica

Ver ejemplo JSON en §17.4. Cada resultado indica `status` (`ok | unavailable | empty | error`), `excluded_rows`, `comparison` opcional y un `format` (tipo + moneda + decimales), **no** un string preformateado.

### 10.6 Métricas de intervalo (riesgo conocido)

MRR, ARR (SaaS) y ocupación (Hotelería) necesitan “expandir” un registro con `inicio`/`fin` a cada período que abarca. **No son agregaciones simples.** Se prevé un nodo `IntervalSum(start, end, value, grain)` en `Expr`, implementado como primitiva del motor (`expand_intervals`). Recomendación: **implementarlo después de estabilizar el core**; en el MVP se entregan `nights` y `adr` (agregaciones simples) y `occupancy` solo si `IntervalSum` ya existe. SaaS queda en V1.1 por este motivo.

---

## 11. Comparaciones temporales

```python
class ComparisonSpec(BaseModel):
    mode: Literal["none","previous_period","previous_week","previous_month","previous_quarter","previous_year"]

class ComparisonResult(BaseModel):
    status: Literal["ok","insufficient_data","previous_zero","not_applicable"]
    previous_value: float | None; delta_abs: float | None; delta_pct: float | None
    previous_range: DateRange | None
    partial_period: bool = False
```

`ComparisonResolver` (`metrics/comparison.py`) recibe el rango actual (filtro de fecha o cobertura total) y `DateCoverage` del dataset y decide:

| Regla | Comportamiento |
|---|---|
| Rango previo cubierto ≥ 80 % por los datos | `ok` |
| Cubierto entre 30 y 80 % | `ok` + warning “el período anterior está parcialmente cubierto” |
| Cubierto < 30 % o sin fechas | `insufficient_data` → la opción del selector aparece **deshabilitada con el motivo** |
| Previo = 0 | `previous_zero`, `delta_pct = null` (nunca ∞) |
| Último período incompleto (ej. mes en curso) | `partial_period = true` |

- `previous_period` es automático por defecto; `none` lo desactiva. Mes, trimestre y año completos usan el período natural anterior; los demás rangos usan una ventana inmediatamente anterior de igual cantidad de días. Los modos explícitos no habilitan ventanas de distinta duración, salvo períodos naturales equivalentes.
- F1 reutiliza MetricEngine/Registry, ComparisonResolver y QuerySpec. ComparisonResult añade `current_range`, `reason_key`, `percentage_reason_key`, `delta_pp`, `direction` y `polarity`; MetricResult conserva el valor actual. `direction` describe cambio; no presupone beneficio empresarial.
- Porcentajes/tasas priorizan puntos porcentuales (`delta_pp`); `delta_abs` conserva la diferencia cruda. Moneda, unidades, conteos y promedios válidos usan variación relativa; con baseline negativo se divide por su magnitud. Baseline cero conserva cambio absoluto y porcentaje nulo. No se devuelven Infinity/NaN.
- Ambas ventanas conservan todos los filtros de segmento. No se inventa un cero para ventanas sin observaciones; tampoco se comparan monedas distintas entre ventanas. Cobertura actual inferior al 30 % impide comparación; inferior al 80 % o período en curso se señala como incompleto. Los umbrales previos siguen la tabla anterior.
- Filtros de fecha sin hora incluyen el día completo en la zona del canonical, tanto en consultas como en exportaciones, incluidos cambios de horario. Timestamps explícitos mantienen su precisión; rangos intradía o de fechas discontinuas no se comparan porque DateRange representa días. La ausencia de fecha devuelve KPI disponible con comparación no aplicable; seleccionar explícitamente un campo temporal inexistente sigue siendo inválido.
- El dashboard devuelve `comparison_options` con `available` y `reason` para cada modo.
- La resolución de la granularidad temporal (`auto`) usa el rango: ≤ 62 días → día; ≤ 2 años → mes (semana si el usuario lo elige); mayor → trimestre/mes.

---

## 12. Filtros

### 12.1 Derivación dinámica (`dashboard/filters.py`)

| Campo | Tipo de filtro |
|---|---|
| `time` (fecha principal o alternativa) | `date_range` con presets (últimos 30/90 días, mes, trimestre, año) |
| `dimension` con cardinalidad ≤ 200 | `multi_select` con valores y conteos |
| `dimension` con cardinalidad > 200 (cliente, transacción) | `search` con autocompletado por `GET …/filters/{field}/options?q=` |
| `measure` (opcional, V1.1) | `numeric_range` |

Se generan **a partir de los campos disponibles + dimensiones custom activas**, ordenados según `profile.bi.extra_filters` y luego por relevancia. No hay lista fija de filtros en código.

### 12.2 Estado y aplicación

```python
class FilterClause(BaseModel):
    field: str                                   # id canónico o custom__slug
    op: Literal["in","not_in","between","gte","lte","contains"]
    values: list[Any]
```

El frontend envía la lista completa de `FilterClause` en cada `POST /dashboard`. El backend los aplica **una vez** a todas las consultas (KPIs, tablas, gráficos, insights, calidad de filas filtradas). El response incluye `row_count` y `filtered_row_count`.

---

## 13. Dashboard dinámico

### 13.1 Plantilla → especificación resuelta

```python
class DashboardTemplate(BaseModel):          # declarado por perfil (y una plantilla base universal)
    sections: list[SectionTemplate]

class SectionTemplate(BaseModel):
    id: str; title_key: str; collapsed: bool = False
    widgets: list[WidgetTemplate]
    visible_if_fields: list[str] = []        # la sección requiere estos campos
```

`DashboardBuilder.build(profile, mapping, availability, filters, comparison)` produce el `DashboardSpec` **resuelto**: solo secciones y widgets cuyas dependencias están disponibles, más `unavailable_metrics`. La condición de visibilidad es **solo “tiene estos campos/métricas”**, sin expresiones ni lógica en la config.

### 13.2 Secciones (módulos)

| Sección | Contenido | Condición |
|---|---|---|
| `executive_summary` | Hasta 6 KPI según `kpi_order` + 3 insights principales | Siempre (≥1 medida) |
| `temporal` | Serie de la métrica principal (+ comparación), selector de granularidad | Campo `time` |
| `breakdown` | **Un widget por dimensión destacada disponible**: barras top-N + participación | ≥1 dimensión |
| `customers` | Ranking y concentración de clientes | `customer_*` |
| `concept_analysis` | Ranking del `concept` (etiqueta según terminología: Producto/Servicio/Habitación) | `concept` |
| `geography` | Ranking por `location` (mapa: V2) | `location` |
| `channel` | Mezcla por canal | `channel` |
| `profitability` | Margen por dimensión | `cost` + `amount` |
| `industry_specific` | Widgets propios del perfil (ADR, ocupación, MRR…) | Según perfil |
| `custom_dimensions` | Desgloses de dimensiones custom | ≥1 custom activa |
| `data_quality` | Tarjeta resumen + enlace al detalle | Siempre |

`ServiceAnalysis` y `ProductAnalysis` **no son módulos distintos**: son `concept_analysis` con distinta terminología (así se evita duplicar lógica).

### 13.3 ¿Dashboard dirigido por configuración? Sí, moderadamente

**Regla:** *la config decide qué y dónde; el código decide cómo.*

- La config puede: elegir secciones, ordenar, escoger tipo de widget **entre los existentes**, indicar métrica/dimensión/top-N, exigir campos.
- La config **no puede**: definir layouts arbitrarios, expresiones o condicionales, ni tipos de widget nuevos. Un tipo de widget nuevo = código de frontend + registro.
- Dos niveles máximos: sección → widget. Sin anidamiento.
- Las plantillas viven como **objetos Python tipados**, no como YAML libre.
- **No** se construye editor de dashboards por el usuario (fuera de alcance).

### 13.4 Componentes reutilizables

Regla: un componente es específico solo si su forma de datos lo es. Todo lo demás se generaliza.

| Componente | Reutilizable | MVP |
|---|---|---|
| `KpiCard` (valor, formato, variación, tooltip) | sí | ✔ |
| `TimeSeriesChart` (línea/área, comparación opcional) | sí | ✔ |
| `BarChart` (horizontal/vertical, top-N, “Otros”) | sí | ✔ |
| `DonutChart` (participación; si hay > 7 categorías se degrada a barras) | sí | ✔ |
| `DataTable` (ordenable, paginación local ≤ 100 filas) | sí | ✔ |
| `RankingList` (barra en línea + valor + participación) | sí | ✔ |
| `InsightList` | sí | ✔ |
| `DataQualityCard` | sí | ✔ |
| `FilterBar` + `DateRangePicker` + `MultiSelectFilter` | sí | ✔ |
| `EmptyState` / `ErrorState` / `LoadingState` (skeletons) | sí | ✔ |
| `ExportButton` | sí | ✔ |
| `Heatmap` (mes × día de semana) | sí | V1.1 |
| `GeoMap` | sí | V2 (requiere geojson y normalización de ubicaciones) |

Todos los gráficos se apoyan en un único `EChartsBase` (import modular de ECharts, solo cliente) y **adaptadores** `ChartResult → EChartsOption` en `components/charts/adapters/`. Ningún componente de gráfico contiene cálculos de negocio.

---

## 14. Insights automáticos (determinísticos)

### 14.1 Dónde vive la lógica

```
bi/insights/
├─ engine.py          # orquesta: ejecuta reglas, puntúa, deduplica, limita
├─ config.py          # umbrales (constantes documentadas)
└─ rules/universal.py # reglas del core
profiles/<id>/insights.py  # reglas propias (opcional)
```

### 14.2 Contrato de regla

```python
class InsightRule(Protocol):
    id: str
    requires: set[str]                              # campos/métricas necesarias
    def evaluate(self, ctx: InsightContext) -> list[Insight]: ...
    # ctx.run(QuerySpec) usa el mismo motor y los mismos filtros activos
```

```python
class Insight(BaseModel):
    id: str; rule_id: str
    severity: Literal["positive","negative","neutral","attention"]
    template_key: str; params: dict                 # el texto se resuelve localizado
    text: str                                       # ya resuelto (con terminología del perfil)
    metric_id: str | None; dimension: str | None
    score: float                                    # para ordenar
```

### 14.3 Reglas universales iniciales

| Regla | Ejemplo | Guarda contra ruido |
|---|---|---|
| `growth_vs_previous` | “Los ingresos crecieron 13 % respecto al período anterior” | Solo si `comparison.status = ok`; umbral ±2 % para no destacar ruido |
| `leader_share` | “{category} concentra 35 % de los ingresos” | Líder ≥ 30 % y ≥ 3 categorías |
| `top_n_concentration` | “Los 5 principales clientes concentran 42 % de la facturación” | ≥ 20 clientes |
| `biggest_decliner` / `biggest_grower` | “{location} cayó 9 %” | Base previa ≥ 5 % del total (evita variaciones enormes sobre bases mínimas) |
| `peak_period` | “Marzo fue el mes de mayor facturación” | ≥ 4 períodos |
| `channel_dominance` | “{channel} representa la mayor proporción de operaciones” | ≥ 2 canales |
| `data_quality_alert` | “El 18 % de las fechas no es válido y no se incluyó” | Solo si supera umbral |

**F2 implementado:** `business.py` extiende `Insight` con `kind`; conserva métricas, dimensión, score y texto, y usa `params` para segmento, valor actual, baseline, deltas, pp, participación, contribución, períodos y filtros. El backend resuelve el texto con terminología del perfil; el frontend lo presenta.

Candidatos: cambio/caída neutral, liderazgo sin empates, concentración individual o Top 3 (más de tres segmentos), cambio por segmento, contribución y divergencia. Los agregados completos se consultan mediante MetricEngine/Registry y los mismos QuerySpec; las comparaciones reutilizan F1. Baseline cero conserva cambio absoluto. Cambios de tasas usan pp. Segmentos sin observaciones comparables no generan cambio relativo.

La contribución requiere una métrica aditiva y que ambos agregados por segmento reconcilien con sus respectivos totales. Se divide el delta del segmento por el delta total; admite aportes negativos y superiores al 100 % del cambio neto. Delta total cero impide la descomposición. Participaciones requieren valores no negativos y una partición aditiva reconciliada. No se infieren causas ni recomendaciones.

Umbrales y pesos viven en `insights/config.py`: cambio mínimo 2 % o 1 pp, peso mínimo de segmento 2 %, concentración mínima 60 %. La divergencia aprobada es facturación/margen bruto con direcciones opuestas, ventanas iguales y poblaciones completas. Score determinístico combina utilidad del tipo, relevancia por `kpi_order` y magnitud normalizada; no representa confianza estadística.

Se ordenan hasta ocho candidatos secundarios; Resultados y Dashboard presentan como máximo tres principales. La identidad incluye tipo, métrica, dimensión y segmento, y el frontend elimina la concentración que ya explica un gráfico visible usando dimensión/segmento o Top N/participación. Las reglas universales anteriores permanecen disponibles para interpretaciones locales.


---

## 15. Exportación, demo e interoperabilidad

### 15.1 Capa de exportación (`analytics_core/exports/`)

```python
class Exporter(Protocol):
    format: str                                    # "csv" | "xlsx" | (futuro) "pdf"
    content_type: str
    def export(self, source: ExportSource, options: ExportOptions) -> Iterator[bytes]: ...
```

Registro por formato → agregar PDF/imagen/informe ejecutivo = nuevo `Exporter` sin tocar rutas.

**MVP:**
- **CSV**: UTF-8 con BOM, delimitador y decimal según `presentation.locale` (para abrir bien en Excel en español).
- **XLSX** (`openpyxl` en modo `write_only`): hojas **Datos**, **Registro de cambios**, **Resumen** (rubro, mapeo, filas, moneda).
- Opciones: alcance (`clean_data` | `filtered_data`), encabezados (`friendly` | `original`), incluir columnas originales/ignoradas, incluir registro de cambios.
- **Seguridad de export:** las celdas de texto que empiecen con `= + - @` (o tab/CR) se prefijan con `'` para evitar inyección de fórmulas (CSV/Excel injection).
- No se guarda el archivo generado: se responde en *streaming* y se descarta.

### 15.2 Estrategia de demo

**La demo entra por el mismo pipeline que un upload; no existe lógica especial dispersa.**

```
backend/demo_data/
├─ retail_demo/    data.csv  demo.json   # {id, name, industry_id, description, preset_mapping?}
├─ services_demo/
└─ hospitality_demo/
```

- `GET /demos` lista los demos (desde `demo.json`).
- `POST /datasets/demo {demo_id}` copia el archivo a una sesión nueva (`DemoSource`) y devuelve la misma respuesta que un upload.
- `preset_mapping` opcional: se aplica con la misma operación que `PUT /mapping` (el usuario igual ve y puede editar el mapeo, o el frontend salta a la revisión con un “Modo demo”).
- Los datasets demo son sintéticos y **son los mismos fixtures de test**: un solo activo, dos usos.

### 15.3 Interoperabilidad entre apps (sin sobreingeniería)

Lo que hay que preparar hoy es **un formato, no una integración**:

```python
class CanonicalManifest(BaseModel):     # analytics_core/canonical/manifest.py
    schema_version: str                  # versionado
    industry_id: str | None
    fields: dict[str, str]               # campo canónico -> columna en el parquet
    custom: list[CustomColumn]
    presentation: PresentationSettings   # moneda, locale, timezone
    row_count: int
    transformations: list[Transformation]
```

Cada sesión ya guarda `canonical.parquet` + este manifiesto. Camino recomendado:

1. **Hoy:** solo mantener el manifiesto versionado y las fronteras de módulo (`analytics_core` no conoce BI).
2. **V2 (sin persistencia en servidor):** opción de exportar **“Paquete de datos”** (Parquet + manifiesto en `.zip`). Las otras apps lo aceptan como fuente y **saltan el mapeo** porque el manifiesto ya lo contiene.
3. **Más adelante (si hay plataforma con backend común):** handoff directo por `dataset_id` dentro del mismo servicio. Requeriría decidir persistencia y consentimiento; hoy no se diseña.

Las otras apps reutilizan `analytics_core` completo (ingesta, mapeo, limpieza, calidad, sesiones, seguridad, exportación) y solo agregan su propia sección en el perfil (`rfm`, `forecast`…).

---

## 16. API

### 16.1 Principios

- Prefijo `/api/v1`. Recurso principal: **`dataset`** (sesión temporal), no “archivo”.
- Todo síncrono en el MVP; la respuesta de dataset incluye `stage` y `expires_at`.
- Mutaciones idempotentes con `PUT` cuando corresponde (mapeo, limpieza).
- Errores con envelope único (§17.2). Warnings **dentro** de respuestas exitosas.

### 16.2 Ciclo de vida de un dataset

```
created ──► parsed ──► mapped ──► validated ──► ready
   │  (upload)  │ (PUT mapping)  │ (POST validate) │ (PUT cleaning opcional / dashboard)
   └────────────┴──── TTL vence o DELETE ──► purged (410 DATASET_EXPIRED)
```

- `dataset_id`: token opaco no adivinable (`secrets.token_urlsafe(24)`), sin significado.
- Cambiar algo *aguas arriba* invalida lo *aguas abajo*: `PATCH source` → se conserva el mapeo por `key` de columna donde coincida y se recalcula `stage`; `PATCH industry_id` → se descarta el mapeo y se re-sugiere.
- Cada acceso renueva el TTL (inactividad), con tope absoluto.

### 16.3 Endpoints

| Método y ruta | Propósito | Request (principal) | Response (principal) |
|---|---|---|---|
| `GET /meta` | Límites y configuración para el frontend | — | `{max_file_mb, allowed_ext, max_rows, ttl_minutes, default_locale, languages}` |
| `GET /profiles` | Rubros disponibles | — | `ProfileSummary[]` (id, nombre, descripción, ícono, fase) |
| `GET /profiles/{id}` | Detalle para el mapeo | — | `ProfilePublic` (campos por nivel, etiquetas resueltas, parámetros) |
| `GET /demos` | Datasets demo | — | `DemoSummary[]` |
| `POST /datasets` | Sube archivo, crea sesión y parsea con valores inferidos | multipart: `file`, `industry_id` | `DatasetResponse` + `source` inferido + `sheets[]` |
| `POST /datasets/demo` | Crea sesión desde un demo | `{demo_id}` | igual que `POST /datasets` |
| `GET /datasets/{id}` | Estado y metadatos | — | `DatasetResponse` |
| `PATCH /datasets/{id}` | Cambiar rubro, `SourceSettings` o `PresentationSettings` | parcial | `DatasetResponse` (+ preview si se reparseó) |
| `GET /datasets/{id}/preview` | Vista previa acotada | `?rows=50&sheet=` | `PreviewResponse` (columnas con `key`, tipo detectado, muestra) |
| `GET /datasets/{id}/mapping` | Sugerencias + mapeo actual | — | `MappingResponse` |
| `PUT /datasets/{id}/mapping` | Guarda y evalúa el mapeo | `MappingRequest` | `MappingResponse` (incidencias + `availability` + preview de desbloqueo) |
| `POST /datasets/{id}/validate` | Construye canonical y valida | `{}` | `ValidateResponse` = `ValidationReport` + `DataQualityReport` + `CleaningPlan` |
| `PUT /datasets/{id}/cleaning` | Aplica la lista completa de acciones elegidas | `{actions:[{id, params}]}` | `CleaningResponse` = `TransformationLog` + calidad actualizada |
| `GET /datasets/{id}/transformations` | Historial de cambios | — | `TransformationLog` |
| `POST /datasets/{id}/dashboard` | Especificación + datos de todos los widgets | `DashboardRequest` | `DashboardResponse` |
| `GET /datasets/{id}/filters/{field}/options` | Autocompletado de valores | `?q=&limit=` | `{values:[{value,count}]}` |
| `POST /datasets/{id}/export` | Descarga (streaming) | `ExportRequest` | archivo CSV/XLSX |
| `DELETE /datasets/{id}` | Borrado inmediato | — | `204` |
| `GET /health` | Salud | — | `{status}` |

### 16.4 Qué cambié respecto a la lista del brief y por qué

| Brief | Decisión |
|---|---|
| `POST /files/upload` | → `POST /datasets` (el recurso es la sesión de dataset) |
| `POST /datasets/{id}/mapping` | → `PUT` (idempotente) |
| `GET /datasets/{id}/quality` | **Sobra**: la calidad viaja en `validate`/`cleaning` y en el widget `quality` del dashboard |
| `GET /datasets/{id}/metrics` | **Se elimina**: la disponibilidad va en `MappingResponse` y los valores en `DashboardResponse` |
| `GET /datasets/{id}/insights` | **Se combina** en el dashboard como widget `insights` (mismos filtros, una sola llamada). Se separa solo si la latencia lo exige |
| `POST /datasets/{id}/clean` | → `PUT …/cleaning` con la lista completa (reconstrucción determinista desde `raw`) |
| `GET …/export` | → `POST` (lleva opciones y filtros en el cuerpo) |
| Endpoint genérico de query | **Post-MVP** (tabla con paginación de servidor / drill-down) |

### 16.5 Síncrono vs asíncrono

| Operación | MVP | Nota |
|---|---|---|
| Upload + sniff + parse a Parquet | Síncrono (≤ límite de tamaño) | Se ejecuta en threadpool, semáforo de concurrencia |
| Mapeo (`PUT`) | Síncrono | Usa muestra para compatibilidad |
| `validate` | Síncrono | Pasada por columnas, memoria acotada |
| `dashboard` | Síncrono | Consultas sobre Parquet ya cargado |
| Export | Streaming | Sin persistir |

Si algún paso supera ~10 s en pruebas, se convierte en job (`stage: "processing"` + polling); el contrato ya contempla `stage`.

---

## 17. Schemas y contrato frontend ↔ backend

### 17.1 Lista de modelos (backend, Pydantic)

| Grupo | Modelos |
|---|---|
| Dataset | `DatasetResponse`, `DatasetMetadata`, `SourceSettings`, `PresentationSettings`, `ColumnMetadata` (key, original_name, detected_type, sample, null_ratio, cardinality) |
| Mapeo | `ColumnMapping` (column_key, target_field?, disposition, options), `MappingRequest`, `MappingSuggestion` (candidates con `score` y `reasons`), `MappingResponse` |
| Validación/calidad | `Issue`, `ValidationReport`, `DataQualityReport`, `QualityScore` (score, band, breakdown) |
| Limpieza | `CleaningActionSpec`, `CleaningPlan`, `Transformation`, `TransformationLog` |
| Perfil | `ProfileSummary`, `ProfilePublic`, `FieldSpec`, `ProfileParameter` |
| Métricas | `MetricDefinition`, `MetricResult`, `ComparisonSpec`, `ComparisonResult`, `UnavailableMetric` |
| Dashboard | `DashboardRequest`, `DashboardSpec`, `SectionSpec`, `WidgetSpec`, `WidgetResult` (union), `ChartResult`, `KpiResult`, `TableResult`, `InsightsResult`, `FilterDefinition`, `FilterClause` |
| Insights | `Insight` |
| Export | `ExportRequest` |
| Errores | `ErrorResponse`, `ErrorDetail`, `Warning` |

### 17.2 Errores y warnings

**Error** (HTTP 4xx/5xx), siempre este envelope:

```json
{
  "error": {
    "code": "MAPPING_TYPE_INCOMPATIBLE",
    "message": "No pudimos interpretar algunos valores de la columna «Precio» como números.",
    "details": [{"column": "c05", "column_name": "Precio", "field": "amount", "count": 132, "ratio": 0.08}],
    "request_id": "9f1c…"
  }
}
```

- `code`: enumeración estable y documentada (contrato). `message`: localizado, sin jerga técnica. `details`: datos estructurados para que la UI pueda resaltar la columna.
- Los errores técnicos (`ValueError`, trazas) **solo** van al log con `request_id`; jamás al cliente.

**Catálogo inicial de códigos:** `FILE_TOO_LARGE`, `FILE_TYPE_UNSUPPORTED`, `FILE_CORRUPT`, `FILE_EMPTY`, `ENCODING_UNDETECTED`, `SHEET_NOT_FOUND`, `TOO_MANY_ROWS`, `TOO_MANY_COLUMNS`, `HEADER_NOT_FOUND`, `MAPPING_MISSING_REQUIRED`, `MAPPING_TYPE_INCOMPATIBLE`, `MAPPING_DUPLICATE_TARGET`, `VALIDATION_FAILED`, `STAGE_NOT_READY` (ej. pedir dashboard sin mapeo), `METRIC_UNAVAILABLE`, `COMPARISON_UNAVAILABLE`, `DATASET_NOT_FOUND`, `DATASET_EXPIRED`, `RATE_LIMITED`, `INTERNAL_ERROR`.

**Warning** (dentro de respuestas 200, lista `warnings[]`):

```json
{"code": "DATE_FORMAT_AMBIGUOUS", "severity": "warning",
 "message": "Interpretamos las fechas como día/mes/año. Podés cambiarlo en la configuración.",
 "column": "c02", "count": null}
```

Widget con problema propio → `WidgetResult.status = "error"` con mensaje local; **el resto del dashboard sigue mostrándose**.

### 17.3 Perfil (lo que recibe el frontend)

```json
{
  "id": "hospitality",
  "name": "Hotelería",
  "fields": [
    {"id": "check_in", "label": "Check-in", "kind": "time", "dtype": "date", "level": "required",
     "description": "Fecha de ingreso del huésped"},
    {"id": "amount", "label": "Ingreso", "kind": "measure", "dtype": "decimal", "level": "required"},
    {"id": "concept", "label": "Habitación", "kind": "dimension", "dtype": "string", "level": "recommended"}
  ],
  "parameters": [{"id": "total_rooms", "label": "Habitaciones disponibles", "type": "integer", "enables": ["occupancy"]}],
  "time_fields": ["check_in", "booking_date"],
  "default_time_field": "check_in"
}
```

El frontend **nunca** recibe métricas ni dashboards del perfil: solo lo necesario para el mapeo.

### 17.4 Métrica

```json
{
  "metric_id": "revenue",
  "label": "Ventas",
  "status": "ok",
  "value": 1523400.5,
  "format": {"type": "currency", "currency": "ARS", "decimals": 0},
  "comparison": {
    "mode": "previous_period", "status": "ok",
    "previous_value": 1348000.0, "delta_abs": 175400.5, "delta_pct": 0.13,
    "previous_range": {"from": "2025-01-01", "to": "2025-03-31"}, "partial_period": false
  },
  "excluded_rows": 12
}
```

No disponible (va a `spec.unavailable_metrics`, no al cuerpo):

```json
{"metric_id": "gross_margin", "label": "Margen bruto", "missing_fields": [{"id": "cost", "label": "Costo"}]}
```

### 17.5 Gráfico (formato neutral, no ECharts)

```json
{
  "widget_id": "revenue_by_month",
  "chart": "timeseries",
  "x": {"type": "time", "grain": "month"},
  "series": [
    {"key": "revenue", "label": "Ventas", "format": {"type": "currency", "currency": "ARS"},
     "points": [["2025-01", 512000], ["2025-02", 498500]]}
  ],
  "comparison_series": [],
  "meta": {"truncated": false, "has_others_bucket": false}
}
```

Desglose por dimensión: `"chart": "breakdown"`, `x: {"type": "category"}`, `points: [["Electrónica", 830000, 0.35], …]` (etiqueta, valor, participación) con `"Otros"` si aplica. El frontend elige barra o dona según `WidgetSpec.chart.variant`.

### 17.6 Filtros

```json
{
  "id": "channel", "field": "channel", "type": "multi_select", "label": "Canal",
  "options": [{"value": "Web", "count": 5210}, {"value": "Tienda", "count": 3120}],
  "default": null
}
```

Tipos: `date_range` (`min`, `max`, `presets`), `multi_select`, `search` (sin `options`; usa el endpoint de opciones).

### 17.7 Dashboard

**Request:**

```json
{
  "filters": [
    {"field": "date", "op": "between", "values": ["2025-01-01", "2025-06-30"]},
    {"field": "channel", "op": "in", "values": ["Web"]}
  ],
  "comparison": {"mode": "previous_period"},
  "time_field": "date",
  "grain": "auto"
}
```

**Response (esqueleto):**

```json
{
  "spec": {
    "profile_id": "retail_ecommerce",
    "sections": [
      {"id": "executive_summary", "title": "Resumen ejecutivo", "widgets": [
        {"id": "kpi_revenue", "type": "kpi", "title": "Ventas", "layout": {"span": 3}},
        {"id": "insights_top", "type": "insights", "title": "Hallazgos", "layout": {"span": 12}}
      ]}
    ],
    "filters": [ … ],
    "unavailable_metrics": [ … ],
    "comparison_options": [
      {"mode": "previous_period", "available": true},
      {"mode": "previous_year", "available": false, "reason": "Los datos no cubren el año anterior."}
    ]
  },
  "data": { "kpi_revenue": {…MetricResult…}, "revenue_by_month": {…ChartResult…} },
  "row_count": 10432, "filtered_row_count": 5210,
  "warnings": [ … ], "generated_at": "2026-01-01T12:00:00Z"
}
```

Cada `data[widget_id]` es un `WidgetResult` con `status`. **La misma respuesta para el mismo (dataset, request)** (determinista) → cacheable en el cliente.

### 17.8 Formato de presentación

El backend devuelve **números crudos + `format`**. El frontend formatea con `Intl.NumberFormat`/`Intl.DateTimeFormat` usando `PresentationSettings.locale` y la moneda. No hay strings preformateados salvo etiquetas y textos de insights.

---

## 18. Frontend

### 18.1 Rutas (App Router) — un paso por ruta

```
/bi                          → elegir rubro + subir archivo o “Probar demo”
/bi/[datasetId]/source       → hoja, encabezado, encoding, separadores (solo si hace falta)
/bi/[datasetId]/mapping      → mapeo de columnas
/bi/[datasetId]/review       → validación, calidad, plan de limpieza
/bi/[datasetId]/dashboard    → dashboard + filtros + exportación
```

El estado del flujo vive en el servidor (dataset) e identificado por URL: los pasos son enlazables y sobreviven a un refresh (mientras no venza el TTL). Prefijo `/bi` para poder montar otras apps en `/rfm`, `/forecast`.

### 18.2 Estructura

```
frontend/src/
├─ app/bi/…                       # páginas finas: componen features
├─ features/
│  ├─ industry-select/  ├─ upload/  ├─ source-settings/
│  ├─ column-mapper/    ├─ data-review/  ├─ dashboard/  └─ export/
│     # cada feature: components/, hooks/, (schemas.ts si hay formularios)
├─ components/
│  ├─ ui/            # Button, Card, Select, Modal, Stepper, Tabs, Tooltip, Banner
│  ├─ charts/        # EChartsBase, ChartFrame, adapters/{timeseries,breakdown,heatmap}.ts
│  └─ data-display/  # KpiCard, DataTable, RankingList, InsightList, DataQualityCard,
│                    # EmptyState, ErrorState, LoadingState
├─ lib/
│  ├─ api/           # client.ts (fetch + manejo de ErrorResponse), endpoints por recurso
│  ├─ format/        # Intl: moneda, número, fecha, porcentaje
│  └─ i18n/          # messages/es.ts, t(), catálogo de códigos de error
├─ types/            # generados desde OpenAPI (no editar a mano)
└─ hooks/            # useDataset, useMapping, useDashboard (envoltorios de TanStack Query)
```

### 18.3 Renderizado del dashboard

`DashboardRenderer` recorre `spec.sections[].widgets[]` y usa un **registro** `type → componente` (`kpi`, `timeseries`, `breakdown`, `ranking`, `table`, `insights`, `quality`, `heatmap`, `geo`). Si llega un `type` desconocido: `ErrorState` discreto para ese widget, sin romper el resto. La grilla usa `layout.span` (12 columnas, responsive).

### 18.4 Estrategia de estado (sin herramientas de más)

| Necesidad | Solución | Razón |
|---|---|---|
| Resultados del backend, caché, revalidación | **TanStack Query** | Es el único agregado que realmente justifica una librería: caché por clave, estados loading/error, invalidación tras mutaciones |
| Identidad del dataset | **URL** (`[datasetId]`) | Persistente, enlazable, sin store |
| Edición del mapeo antes de guardar | `useReducer` local en `column-mapper` | Estado efímero de un solo componente; se envía con `PUT` |
| Filtros y comparación del dashboard | `useState`/`useReducer` en la página + un `DashboardFiltersContext` | Solo lo usan `FilterBar` y el hook de dashboard |
| Configuración regional/idioma | Context mínimo | Estable y global |
| **No se usa Zustand/Redux** | — | No hay estado global compartido entre features que lo justifique |

**Claves de TanStack Query:** `['dataset', id]`, `['dataset', id, 'preview', …]`, `['dataset', id, 'mapping']`, `['dataset', id, 'dashboard', hash(request)]`.
- `staleTime: Infinity` para datos de un dataset (el servidor es determinista); se **invalidan** con el prefijo `['dataset', id]` tras `PATCH`/`PUT`/limpieza.
- Dashboard: `placeholderData: keepPreviousData` para evitar parpadeo al cambiar filtros; `hash(request)` estable (orden de claves normalizado).
- Errores `DATASET_EXPIRED`/`DATASET_NOT_FOUND` → redirección a `/bi` con mensaje claro; banner de “Tu sesión vence en X min” usando `expires_at`.

### 18.5 Formularios y validación en cliente

Validación del cliente **solo para UX** (extensión, tamaño según `/meta`, campos requeridos del mapeo). La validación real es del backend; nunca se confía en el cliente.

---

## 19. Seguridad y privacidad

### 19.1 Archivos subidos (`analytics_core/security/upload_guard.py`)

| Control | Implementación |
|---|---|
| **Tamaño máximo** | Rechazo por `Content-Length` **y** lectura en *streaming* por chunks abortando al superar el límite (no confiar en el header); límite también en el proxy inverso |
| **Extensiones permitidas** | Lista blanca `.csv`, `.xlsx`. Rechazo explícito de `.xls`, `.xlsm`, `.xlsb`, `.ods`, ejecutables, comprimidos |
| **Validación real del tipo** | No se confía en extensión ni en `Content-Type`. **XLSX:** debe ser ZIP válido (`PK\x03\x04`) que contenga `[Content_Types].xml` y `xl/workbook.xml`. **CSV:** sin bytes NUL, decodificable como texto |
| **Anti “zip bomb” (XLSX)** | Límite de entradas del ZIP (≤ 1000), tamaño descomprimido total (≤ 100 MB) y ratio de compresión (≤ 100:1) verificados **antes** de abrir con `openpyxl` |
| **Macros / contenido activo** | Rechazar `.xlsx` con `xl/vbaProject.bin`, `externalLinks/` u objetos OLE incrustados |
| **XML seguro** | Instalar `defusedxml` (openpyxl lo usa si está presente) para evitar XXE / billion-laughs |
| **Fórmulas** | Se leen valores en caché (`data_only=True`); jamás se evalúan fórmulas |
| **Nombre de archivo** | El nombre original **no se usa** para el sistema de archivos: se guarda como `source.bin` dentro de la carpeta de sesión. Para mostrar/exportar: `Path(name).name`, sin caracteres de control, longitud ≤ 100 |
| **Path traversal** | Toda ruta se construye únicamente desde `SESSIONS_ROOT / <id validado por regex>`; se verifica que la ruta resuelta quede dentro de la raíz |
| **Almacenamiento temporal** | Directorio dedicado, permisos `0700`, fuera del árbol servido; eliminación al vencer TTL, en `DELETE`, y **barrido al arrancar** el servicio |
| **Límites de memoria** | Límites de filas/columnas/tamaño (§20), semáforo de concurrencia y límite de memoria del contenedor |
| **Uploads abusivos** | Rate limit por IP (p. ej. 10 uploads/hora, configurable), máximo de sesiones activas global y por IP, timeouts de request, CORS restringido a los orígenes propios, cabeceras de seguridad. Para el sitio público con demo: Cloudflare Turnstile (o similar) como mejora opcional |
| **Manejo seguro de errores** | Sin trazas ni rutas en respuestas; `request_id` para correlación |
| **Inyección en export** | Prefijo `'` en celdas que empiecen con `= + - @` (§15.1) |

### 19.2 Privacidad (ciclo temporal)

```
Upload → source.bin (temporal) → raw.parquet → canonical.parquet → análisis → fin de sesión → purge
```

- En cuanto se genera `raw.parquet`, **`source.bin` se elimina** (el original ya no se necesita).
- **TTL por inactividad** (p. ej. 60 min) + **tope absoluto** (p. ej. 4 h), aplicado por: (a) comprobación en cada acceso, (b) tarea periódica `reaper` (cada pocos minutos), (c) barrido al iniciar.
- `DELETE /datasets/{id}` = borrado inmediato (botón “Terminar y borrar mis datos”).
- **Los logs nunca contienen valores de celdas ni nombres de archivo originales** (solo tamaños, conteos, códigos y `request_id`). Los `examples` del log de transformaciones existen solo en la sesión.
- No hay analítica que capture contenido; no hay backups de sesiones.
- Texto claro en la UI: “Tus datos se procesan de forma temporal y se eliminan al terminar (máx. X min de inactividad)”.
- **Despliegue:** por depender de estado temporal en disco, el backend requiere un **proceso persistente en contenedor** con un solo worker o volumen efímero compartido (no un entorno serverless sin disco persistente por request). El frontend puede alojarse en cualquier hosting de Next.js.

---

## 20. Archivos grandes

| Parámetro (configurable en `settings.py`) | Valor inicial |
|---|---|
| Tamaño máximo de archivo | **20 MB** |
| Filas máximas | **250 000** |
| Columnas máximas | **200** |
| Filas de vista previa | 50 |
| Muestra para inferencia/perfilado | hasta 20 000 filas (inicio + aleatorio reproducible) |
| Concurrencia de procesamiento pesado | 2 simultáneos (semáforo) |
| Memoria estimada | pandas ≈ 5–10× el tamaño del CSV → 20 MB ≈ 100–200 MB por sesión |

**Estrategia por etapas:**
1. **Sniffing** con los primeros bytes/filas (barato).
2. **Lectura a texto** y escritura inmediata a **Parquet** (deja de vivir en memoria); las siguientes etapas cargan del Parquet **por columnas** (`columns=[…]`).
3. **Perfilado y sugerencia de mapeo** sobre la **muestra**.
4. **Parseo/validación completa** columna por columna (una pasada por columna, no toda la tabla a la vez); tipos `category` para texto de baja cardinalidad.
5. **Consultas del dashboard** sobre `canonical.parquet` leyendo solo las columnas necesarias.

**Principio: nunca se calculan KPIs sobre una muestra.** El muestreo se usa solo para vista previa, inferencia de formatos y sugerencias. Si el archivo supera los límites, se **rechaza** con un mensaje claro (“El archivo tiene 480 000 filas; el máximo actual es 250 000”) en lugar de analizar un subconjunto y devolver totales incorrectos.

Las tareas de CPU se ejecutan en threadpool (`run_in_threadpool`) para no bloquear el event loop de FastAPI.

---

## 21. Errores, i18n y configuración regional

### 21.1 Sistema de errores

Jerarquía en `analytics_core/errors.py`:

```
AppError(code, http_status, message_key, params, details)
├─ FileError (FILE_*, ENCODING_*, SHEET_*, TOO_*)
├─ MappingError (MAPPING_*)
├─ ValidationError_ (VALIDATION_*)
├─ DatasetError (DATASET_NOT_FOUND, DATASET_EXPIRED, STAGE_NOT_READY)
├─ MetricError (METRIC_UNAVAILABLE, COMPARISON_UNAVAILABLE)
└─ RateLimitError
```

- **Frontera de traducción:** todo código que llama a pandas/openpyxl/zipfile envuelve las excepciones técnicas y las convierte en `AppError` con `message_key` amigable. Ningún `ValueError` de librería llega al handler global.
- Handler global: `AppError` → envelope §17.2; excepción desconocida → `INTERNAL_ERROR` genérico + traza en log con `request_id`.
- El frontend tiene un **catálogo `code → mensaje`** propio (i18n) como fuente primaria de textos y usa el `message` del backend como respaldo.

### 21.2 Internacionalización

- **Backend:** `messages/es.json` (y `en.json` a futuro) con claves para errores, warnings, etiquetas de métricas, plantillas de insights. `translate(key, locale, **params)`; el locale llega en `Accept-Language`. Terminología del perfil según §5.2.
- **Frontend:** diccionario tipado `messages/es.ts` + helper `t('clave', params)`. **Ningún texto visible hardcodeado en componentes** (regla del implementador). Migración a `next-intl` cuando exista inglés, sin cambiar las claves.
- **Separación de idioma y formato:** el *idioma de la UI* (`Accept-Language`) es independiente de la *configuración regional de los datos* (`PresentationSettings`).

### 21.3 Configuración regional y moneda

Dos objetos distintos (no mezclarlos):

```python
class SourceSettings(BaseModel):          # cómo LEER el archivo
    encoding: str; delimiter: str | None
    sheet: str | None; header_row: int | None
    decimal: Literal[",","."]; thousands: Literal[".",",","'"," ",""]
    date_dayfirst: bool; date_format: str | None
    column_overrides: dict[str, ColumnParseOverride] = {}

class PresentationSettings(BaseModel):    # cómo MOSTRAR los resultados
    currency: str = "ARS"                 # ISO 4217 (ARS, USD, EUR, BRL…)
    locale: str = "es-AR"
    timezone: str = "America/Argentina/Buenos_Aires"
```

- El valor monetario (`amount`) es un número; **la moneda es un atributo de presentación**. Sin conversión de divisas.
- Si existe columna `currency` con más de un valor: warning `MIXED_CURRENCY` y el dashboard **exige** un filtro de moneda única antes de totalizar (evita sumar ARS + USD).
- Fechas sin zona horaria se tratan como fechas locales naive (agrupación por día sin desplazamientos). Si el dato trae zona, se convierte a `timezone` antes de truncar a día.

---

## 22. Responsive y accesibilidad

**Responsive**
- Objetivo: notebook, desktop y tablet. Grilla de 12 columnas: KPI 3 col (≥ 1024 px) → 6 col (tablet) → 12 col (móvil).
- Móvil completo es secundario, pero **nunca inutilizable**: gráficos con altura mínima y ancho fluido, tablas con scroll horizontal contenido, `FilterBar` colapsable en un panel, mapeo apilado (campo arriba, selector abajo).

**Accesibilidad (mínimos)**
- Contraste AA en texto y gráficos; paleta apta para daltonismo.
- **No depender solo del color:** ECharts con `aria` y `decal` (patrones), etiquetas de datos/valores y leyendas textuales; variación con **flecha + signo**, no solo verde/rojo.
- Todos los controles con `label`; foco visible; orden de tabulación lógico; el mapeo y los filtros operables por teclado.
- Cada gráfico incluye descripción alternativa (`aria-label`/texto) y una vista de tabla accesible (“Ver como tabla”).
- Estados de carga/error anunciados con `aria-live`.

---

## 23. Testing

### 23.1 Backend (`pytest`, `httpx` TestClient)

| Nivel | Cobertura |
|---|---|
| **Unit** | `ingestion` (encodings, delimitadores, decimales, fechas ambiguas, encabezados duplicados), `mapping` (puntaje, resolución global, conflictos), `quality` (cada check), `cleaning` (cada acción + impacto estimado + log), `metrics` (cada `Expr` y cada métrica con datos mínimos), `comparison`, `insights` (umbrales), `filters`, `security` (nombres, rutas, celdas de export) |
| **Integration** | Flujo completo por API con fixtures: upload → mapping → validate → cleaning → dashboard → export; TTL/purge; errores con envelope correcto |
| **Contrato (perfiles)** | Para **cada** perfil registrado: métricas/campos existentes, alias sin colisiones, `primary_date` válido, terminología completa |
| **Uploads** | Archivo demasiado grande; extensión renombrada (`.exe` → `.csv`); XLSX falso; zip bomb; xlsm con macros; CSV con NUL; nombre con `../`; export con `=cmd()` |
| **Snapshots** | `DashboardSpec` por perfil/fixture (detecta cambios accidentales de estructura) |

### 23.2 Frontend

| Herramienta | Qué |
|---|---|
| Vitest + Testing Library | `column-mapper` (sugerencias, conflictos, panel “se habilita…”), `FilterBar`, `KpiCard` (variación, formato), estados `Empty/Error/Loading`, `DashboardRenderer` con specs sintéticos (widget desconocido, widget en error, sección vacía) |
| MSW | Mock del API con los mismos JSON de §17 |
| Tests de adaptadores | `ChartResult → EChartsOption` (puros, sin DOM) |
| Accesibilidad | `jest-axe` en páginas principales |

### 23.3 End-to-end (Playwright)

Flujo: **seleccionar industria → cargar archivo → mapear → validar → dashboard → exportar**, con datasets pequeños. Se ejecuta por cada fixture (retail, servicios, hotelería) y para el camino **“Probar demo”**. Verifica además que se ven/no se ven las secciones esperadas por perfil y que el archivo exportado abre y contiene las hojas esperadas.

### 23.4 Fixtures multi-industria (prueba de desacople)

Los tres fixtures están diseñados para **romper** un core acoplado a Retail:

| Aspecto | Retail / E-commerce | Servicios | Hotelería |
|---|---|---|---|
| Formato | CSV `;`, latin-1, decimal `,`, fechas `dd/mm/aaaa`, `$ 1.234,50` | XLSX de 2 hojas, encabezado en la fila 3, fechas reales de Excel | CSV `,`, UTF-8, fechas ISO |
| Columnas clave | `fecha_compra, codigo_factura, articulo, cant, valor_total, costo_unit, provincia, vendedor, canal` + custom `campaña_marketing` | `fecha, cliente, servicio, profesional, tarifa, duracion_hs, proyecto, estado, importe` | `reserva, fecha_reserva, check_in, check_out, tipo_habitacion, huespedes, noches, tarifa, canal, moneda` |
| Sin… | — | **sin cantidad, sin costo, sin producto** | **sin cliente**, **dos fechas** (elección de `time_field`), noches derivable |
| Casos sucios | 50 duplicados exactos, 11 fechas inválidas, 7 importes negativos, encabezados con espacios | fila de totales al final, categorías con variantes (“Consultoria”/“Consultoría”), columna vacía | `check_out ≤ check_in` en algunas filas, `noches` inconsistente, mezcla ARS/USD |
| Prueba especialmente | métricas con costo, mapeo por alias raros (`cant`), `cost basis` | dashboard sin cantidad ni producto; hojas múltiples | fecha alternativa, derivados, ADR, `ProfileCheck`, moneda mixta |

Cada fixture incluye un **archivo limpio** y uno **sucio**, y un `expected.json` con KPIs esperados (tests deterministas).

**Tests de “regla arquitectónica” (`tests/contract/test_core_decoupling.py`):**
1. Registra en runtime un perfil sintético `_test_industry` (sin tocar el core) y corre el pipeline completo sobre un CSV inventado: debe funcionar.
2. `import-linter`: falla si `analytics_core` importa `bi`, si algo fuera de `pandas_impl` importa pandas, o si `profiles` importa `api`.
3. Búsqueda textual: ningún literal de industria en `analytics_core/` ni en `bi/{metrics,dashboard,insights}/*.py` (salvo `profiles/`).
4. Comprobación de PR: si un cambio que agrega un perfil modifica archivos del core, el CI avisa (regla 5.4).

---

## 24. Observabilidad (MVP simple)

| Qué | Dónde | Cómo |
|---|---|---|
| **Logging** | `analytics_core/logging.py` | Logging estándar en JSON; `request_id` (middleware, cabecera `X-Request-ID`) en cada línea; niveles coherentes. **Sin valores de celdas ni nombres de archivo** |
| **Errores** | `api/main.py` (handler global) | Traza completa al log + `request_id`; al cliente solo el envelope |
| **Timing** | `timed("stage")` (context manager) | Registra etapa, duración, filas y columnas: `sniff`, `read_raw`, `build_canonical`, `validate`, `query`, `export`. Opcional: cabecera `Server-Timing` |
| **Warnings** | `WarningCollector` por request | Acumula avisos durante el pipeline y los devuelve en `warnings[]`; también se cuentan en log |
| **Métricas operativas** | Eventos de log estructurado | Uploads, fallos por `code`, duración p50/p95 por etapa, sesiones activas, purgas por TTL |
| **Más adelante** | — | Sentry / OpenTelemetry cuando haya tráfico real (no en el MVP) |

---

## 25. Roadmap de implementación (orden sugerido)

| Fase | Entregable | Criterio de aceptación |
|---|---|---|
| **0. Esqueleto** | Repo, backend/frontend mínimos, CI, `import-linter`, logging, envelope de errores, `/meta`, `/health`, generación de tipos TS | CI verde; una llamada de ejemplo end-to-end tipada |
| **1. Ingesta** | Upload seguro, sniffing, lectura a Parquet, sesiones + TTL + reaper, `preview`, `PATCH source` | Los 3 fixtures se cargan (incluido latin-1/`;`/multi-hoja); tests de uploads maliciosos pasan |
| **2. Perfiles y mapeo** | `IndustryProfile`, registro, perfil `custom` primero, matcher, `PUT mapping`, UI del mapeo con panel de desbloqueo | Sugerencias correctas sobre fixtures; conflictos detectados |
| **3. Canonical + validación + calidad + limpieza** | `build_canonical`, checks, score, plan, `PUT cleaning`, log de transformaciones | Reconstrucción determinista; “volver al original” funciona |
| **4. Motor de consultas y métricas** | `QuerySpec`, `PandasEngine.run_query`, `Expr`, métricas universales, disponibilidad, comparaciones | Métricas con valores esperados de `expected.json` |
| **5. Dashboard, filtros e insights** | `DashboardBuilder`, widgets, filtros, insights universales, `DashboardRenderer`, componentes y adaptadores ECharts | Los 3 rubros generan dashboards distintos sin cambiar el core |
| **6. Perfiles MVP** | `retail_ecommerce`, `services`, `hospitality` con sus métricas, alias, plantillas y tests | Regla 5.4 cumplida (solo agregar carpeta de perfil) |
| **7. Export y demo** | Exporters CSV/XLSX, demos, “Probar demo” | E2E completo con demo y con archivo propio |
| **8. Endurecimiento** | Rate limiting, límites, accesibilidad, responsive, E2E Playwright, documentación | Checklist de §19 y §22 completo |
| **V1.1** | `IntervalSum` → MRR/ocupación, perfiles restantes, plantillas de mapeo en localStorage, Heatmap, tabla con paginación de servidor | — |

---

## 26. Supuestos, riesgos y fuera de alcance

### Supuestos (ajustables)
- Los límites de §20 son razonables para un producto comercial inicial; se calibran con datos reales.
- El backend correrá como **un único proceso/contenedor persistente** en el MVP.
- La UI y los mensajes son en español (`es-AR` por defecto); el inglés llega después sin cambiar claves.
- Los datos analizados son transaccionales o casi (una fila = línea de operación); no se contemplan cubos ya agregados.

### Riesgos principales
| Riesgo | Mitigación |
|---|---|
| **Interfaz de `DataEngine` demasiado amplia o filtrándose pandas** | `import-linter`; métodos declarativos (`checks`, `action`, `QuerySpec`) |
| **Métricas de intervalo (MRR/ocupación)** no encajan en agregaciones simples | Diferidas; `IntervalSum` explícito (§10.6) |
| **Falsa precisión** del score y de las sugerencias de mapeo | Banda + desglose + `reasons`; siempre confirmación del usuario |
| **Ambigüedad semántica** (costo unitario vs total, descuento % vs monto, fecha día/mes) | Opciones de mapeo (§4.7) y preguntas explícitas; nunca supuestos en silencio |
| **Sumar monedas distintas** | `MIXED_CURRENCY` bloquea totales hasta filtrar por moneda |
| **Config-driven que crece hacia un “motor genérico”** | Límites de §13.3; nuevos tipos de widget = código |
| **Estado en disco en despliegues multi-instancia** | Un worker en el MVP; volumen compartido o afinidad de sesión si se escala |

### Fuera del MVP (explícito)
Autenticación y roles · pagos · multi-tenancy · persistencia de datasets · IA generativa · conectores (Sheets/SQL/Shopify/ERP…) · forecasting, RFM, churn, anomalías, sentimiento, tests estadísticos · mapas geográficos · PDF/informes · edición de dashboards por el usuario · conversión de divisas · `.xls/.xlsm/.ods`.

---

## 27. Reglas para el implementador

1. **Solo `analytics_core/engine/pandas_impl/` importa pandas/numpy.** Todo lo demás habla con `DataEngine`.
2. **El frontend no calcula métricas.** Si necesita un número, viene del backend.
3. **Ningún texto visible hardcodeado** en componentes ni en mensajes de backend: siempre claves i18n + terminología del perfil.
4. **Nada de literales de industria** en el core (`analytics_core`, `bi/{metrics,dashboard,insights}`).
5. **Agregar una industria = solo carpeta de perfil + tests.** Si hace falta tocar el core, se corrige el core.
6. **Los filtros se aplican una vez**, en `dashboard_service`, mediante `QuerySpec.filters`.
7. **Nunca modificar datos sin registrar** un `Transformation`. Detectar (`Issue`) y cambiar (`Transformation`) son cosas distintas.
8. **Filas inválidas no se borran**: se excluyen por métrica y se informa `excluded_rows`.
9. **Nunca calcular sobre muestras**; las muestras son solo para vista previa e inferencia.
10. **Errores técnicos nunca llegan al usuario**; todo pasa por `AppError` con `code` estable.
11. **Los logs no contienen datos del cliente** (ni valores de celdas ni nombres de archivo).
12. **Tipos TS generados desde OpenAPI**; no duplicar modelos a mano.
13. **Cada métrica, check, acción de limpieza, regla de insight y perfil** viene con su test.
14. **Sin sobreingeniería**: nada de colas, microservicios, ORMs, ni librerías de estado global en el MVP. Si algo de este documento parece requerir una, es señal de malinterpretación.

