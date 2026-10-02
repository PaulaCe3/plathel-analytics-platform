# PLATHEL — contexto

PLATHEL ayuda a personas no técnicas a entender sus datos y estimar qué puede pasar después. La potencia técnica permanece detrás de una experiencia simple, con resultados claros y una acción principal por pantalla.

- Marca: PLATHEL; descriptor DATA · AI · AUTOMATION.
- Identidad aceptada: Mineral/Mar, composición editorial minimalista, Space Grotesk + Inter y dataviz verde musgo. Tokens y componentes en [DESIGN_SYSTEM.md](DESIGN_SYSTEM.md).
- Experiencia pública actual: elegir una demo precargada → procesamiento automático → Resultados → Dashboard en `/bi`; forecast integrado en Resultados, con `/forecast` conservado como entrada compatible. Responsabilidades internas separadas.
- `analytics_core` reúne capacidades reutilizables; BI y forecast no se importan entre sí. El backend calcula y el frontend representa. Se reutilizan ingestión, preparación y sesiones.


## Visión de producto

Experiencia visible definitiva confirmada:

1. **Elegir demo:** seleccionar un ejemplo precargado del rubro, sin cargar datos propios ni configurar el análisis.
2. **Resultados + Predicciones:** entender qué está pasando y qué puede estimarse; explicar por qué una predicción no está disponible cuando corresponda.
3. **Dashboard:** explorar resultados de forma interactiva, con filtros y exportación.

La potencia técnica permanece detrás de una experiencia extremadamente simple para usuarios no técnicos. Cada pantalla debe aclarar dónde está la persona, qué ve, qué significa y cómo continuar.

- Interpretaciones breves de gráficos: una o dos frases basadas en resultados, sin inventar causas.
- Predicciones en lenguaje humano: qué se estima, horizonte, historial usado, evaluación y límites; nunca certezas.
- Dashboard interactivo con pocos indicadores y gráficos relevantes inicialmente.
- Progressive disclosure: detalles, opciones secundarias y explicación del modelo se muestran solo cuando se necesitan.
- Evitar terminología técnica innecesaria en la experiencia principal.

PLATHEL público es actualmente una demo simplificada con datasets precargados. El visitante no carga datos propios: elige un ejemplo, PLATHEL lo procesa y abre Resultados; luego puede explorar el Dashboard. La infraestructura de ingestión, Autopilot, mapping, validación y limpieza permanece interna para futuras implementaciones reales adaptadas a cada empresa.

## Consulta especializada
- [Estado implementado y límites](knowledge/CURRENT_STATE.md): buscar la funcionalidad; snapshot fechado, no evidencia de ejecución en la sesión actual.
- [Decisiones aceptadas](DECISIONS.md), [arquitectura y reglas](ARCHITECTURE.md), [diseño](DESIGN_SYSTEM.md).
- [Operación y comandos](../README.md); [trabajo futuro aprobado](knowledge/ROADMAP.md), solo para planificación. No hay trabajo adicional confirmado en el snapshot actual; el prompt determina la fase.

Esta memoria se versiona con el código y usa Markdown estándar compatible con Obsidian, sin dependencia operativa de esa herramienta. No reemplaza las fuentes especializadas.
