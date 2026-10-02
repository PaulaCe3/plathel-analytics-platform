# PLATHEL — mapa para Codex

## Consulta según la tarea
No leer toda la memoria por defecto; consultar solo lo pertinente:
- Producto, UX o alcance: [docs/CONTEXT.md](docs/CONTEXT.md).
- Backend, datos, API o contratos: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md); contiene reglas y mapa de secciones de la arquitectura oficial.
- UI, marca, componentes o accesibilidad: [docs/DESIGN_SYSTEM.md](docs/DESIGN_SYSTEM.md).
- Decisiones y restricciones aceptadas: buscar el tema en [docs/DECISIONS.md](docs/DECISIONS.md).
- Funcionalidades implementadas y límites: buscar el tema en [docs/knowledge/CURRENT_STATE.md](docs/knowledge/CURRENT_STATE.md).
- Planificación solamente: [docs/knowledge/ROADMAP.md](docs/knowledge/ROADMAP.md).
- Instalación, comandos y operación: sección pertinente de [README.md](README.md).

## Trabajo localizado
- Revisar `git status` antes de modificar; conservar trabajo previo y contratos funcionales.
- Empezar por los archivos mencionados en la tarea. Buscar con `rg` antes de leer archivos completos; leer solo rangos/secciones relevantes.
- Expandir la exploración solo cuando sea necesario. No escanear todo el repositorio salvo necesidad estricta.
- Preferir cambios mínimos y localizados; no modificar archivos no relacionados.
- Reutilizar componentes y abstracciones existentes antes de crear nuevas.
- La fase actual la define el prompt. No avanzar de fase ni agregar microservicios, ORM, base de datos, colas, autenticación, pagos, LLM o infraestructura no solicitada.
- Ejecutar primero los tests más específicos; suite completa solo si el cambio lo justifica. Para cambios de código ejecutar import-linter; lint/typecheck/build cuando corresponda. Para documentación verificar rutas y `git diff --check`.
- No declarar una función verificada sin ejecutarla.
- No explicar comandos rutinarios; informar bloqueos importantes. Respuesta final breve, máximo 20 líneas.
- No hacer commits ni push salvo pedido explícito del usuario.

## Memoria versionada
Actualizar solo información que cambió en su fuente correspondiente; enlazar en lugar de duplicar. Mantenerla breve, factual y útil, sin logs, razonamientos internos ni diario. La memoria vive en Markdown del repositorio; `.obsidian/` es configuración personal no versionada. No instalar plugins ni depender de APIs externas para usarla.
