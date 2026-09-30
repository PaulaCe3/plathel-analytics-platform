# DATA ANALYTICS PLATFORM — Repository Instructions

## Source of truth
La arquitectura oficial vive en:
docs/arquitectura_bi_multiindustria.md

Para cada tarea, lee solo las secciones relevantes de ese documento, no todo el archivo salvo que sea necesario.

## Memoria persistente
Antes de una tarea importante, leer:
- docs/knowledge/PLATHEL_CONTEXT.md
- docs/knowledge/PRODUCT_VISION.md
- docs/knowledge/DECISIONS.md
- docs/knowledge/CURRENT_STATE.md

Leer ROADMAP.md solo cuando la tarea afecte planificación. Después de una implementación importante, actualizar únicamente los documentos cuya información cambió. Mantener memoria breve, factual y útil: enlazar documentación existente; no duplicarla, guardar logs ni razonamientos internos, ni convertir la memoria en un diario.

La memoria se versiona con el código. La configuración personal `.obsidian/` no se versiona. No instalar plugins ni depender de APIs externas para usar esta memoria.

## Architectural rules
- analytics_core nunca importa bi.
- pandas/numpy solo pueden importarse dentro de analytics_core/engine/pandas_impl/.
- API: routers → services → core. Los routers no contienen lógica de negocio.
- El backend calcula la lógica analítica; el frontend renderiza.
- Los contratos TypeScript se generan desde FastAPI/OpenAPI. No duplicar modelos manualmente.
- raw.parquet nunca se modifica.
- canonical se reconstruye desde raw + mapping + configuración + acciones.
- Issue y Transformation son conceptos distintos.
- Ninguna transformación de datos puede ser silenciosa.
- No agregar microservicios, ORM, base de datos, colas, autenticación, pagos, LLM ni infraestructura no solicitada.
- No implementar funcionalidades de fases posteriores.
- Agregar una industria no debe requerir modificar analytics_core.

## Workflow
Antes de modificar:
1. revisar git status;
2. inspeccionar implementación existente;
3. conservar contratos funcionales.

Después de modificar:
- ejecutar los tests relevantes;
- ejecutar import-linter;
- ejecutar lint/typecheck/build solo cuando corresponda;
- no declarar una función como verificada sin haberla ejecutado.

## Scope
La fase actual siempre está definida por el prompt de la tarea.
No avanzar a la fase siguiente sin autorización explícita.

## Responses
Trabaja sin narrar cada comando.
Informa solo bloqueos importantes.
El informe final debe ser breve: máximo 20 líneas.
