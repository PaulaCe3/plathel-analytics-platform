# PLATHEL — sistema visual

Alcance: Análisis y Predicciones. Wordmark textual temporal: no hay isotipo oficial en el repositorio. UI compartida en `packages/ui`; backend descriptivo y forecasting independientes. La ingestión, preparación, exportaciones, sesiones y seguridad existentes se conservan.

## Auditoría y decisiones

- Marca previa, colores verdes/azules y superficies inconsistentes → PLATHEL, descriptor DATA · AI · AUTOMATION y tokens minerales.
- Selectores de columnas, claves internas y scores dominantes → resumen de identificadas; ambiguas visibles; todas las selecciones disponibles en Ver todas. La propuesta y el payload existentes no cambian. La clasificación visual usa la confianza entregada por backend y los conflictos.
- Revisión técnica con acciones cero/observaciones abiertas → mejoras relevantes, observaciones colapsadas y cambios realizados accesibles. Eliminaciones nunca preseleccionadas; requieren diálogo explícito antes de llamar al endpoint.
- Todos los widgets simultáneos → hasta cinco KPIs según el orden del backend; Resultados muestra hasta cuatro gráficos clave seleccionados por backend y Dashboard prioriza uno principal y dos secundarios, hasta tres hallazgos y un desglose seleccionable colapsado. Resto de métricas/detalles disponibles. Las interpretaciones reutilizan reglas determinísticas del backend con los mismos filtros. No se calculan conclusiones en frontend.
- Export con todas las opciones abiertas → diálogo nativo, formato/alcance primero, opciones avanzadas colapsadas. Mismo payload y filtros del resultado mostrado; descarga bloqueada mientras se actualizan filtros.

## Tokens

| Token | Valor | Uso |
|---|---|---|
| Deep Rock | #141616 | Textos, acción principal |
| Wet Graphite | #404245 | Textos secundarios, gráficos, foco |
| Basalt Grey | #5F5D5C | Textos auxiliares |
| Cold Platinum | #B9BABA | Bordes, estados neutros |
| Sea Mist | #D1D3D3 | Divisores, superficies |
| Foam White | #EEEFEF | Superficie principal |

Estados funcionales sobrios: rojo para error, ocre para advertencia, verde para éxito; siempre acompañados de texto. Space Grotesk para títulos e Inter para cuerpo, alojadas localmente con licencias OFL; títulos 30–44px internos/38–64px home; cuerpo 14–16px. Espaciado base 24px, controles mínimo 44px, radios 6px. Sin sombras decorativas ni gradientes.

## Primitives y patrones

`packages/ui/src/primitives.tsx` (reexportado por BI): Button (primary/secondary/ghost, busy/disabled), Card (sección con divisor), Input, Select, Status, Toast (info/success/error), SectionHeader, EmptyState, ErrorState con retry, LoadingState y Dialog.

`packages/ui/src/product-header.tsx`: marca y navegación Datos → Resultados → Dashboard; `product-navigation.tsx`: adaptación y Stepper. Columnas y preparación pertenecen al primer momento; pasos futuros no son enlaces que permitan saltar validaciones. Los completados/actuales llevan texto accesible, sin depender del color.

Dialog usa HTML dialog/showModal: foco modal, tabulación contenida, Escape, botón Cerrar y retorno de foco al disparador. Está etiquetado por título. Export y confirmación de transformaciones destructivas reutilizan el mismo patrón. Loading/error/toasts usan status/alert y aria-live; botones ocupados deshabilitados. Siempre usar label o aria-label en Input/Select.

DashboardRenderer y estados de widgets reutilizan las mismas primitives; no hay un segundo juego de EmptyState/ErrorState. ECharts mantiene aria/decal, ResizeObserver y alternativa de tabla de los mismos puntos. Comparaciones muestran flecha, signo, porcentaje y texto. Los gráficos usan verde musgo: #3F4D3B, #596B52, #75866C, #98A590 y #BEC6B8. Forecast distingue historial oscuro y futuro discontinuo; no dibuja intervalos inexistentes.

Responsive: shell máximo 1280px, padding 40/24/20px; columnas y filtros se apilan en móvil. Tabla con scroll local. Grid de KPIs mantiene span 12 móvil, 6 tablet y span definido por backend en desktop. Todos los controles conservan foco visible; spinner y scroll respetan reduced-motion.

## Predicciones

Comparte cabecera, estilos, fuentes, controles y EChartsBase. Resultados integra «Qué podría pasar después» y crea una primera estimación si los datos son compatibles; en caso contrario explica el límite. Conserva la sesión preparada. Los resultados muestran período observado, horizonte, tabla alternativa, evaluación histórica y límites; el detalle del modelo queda colapsado. La base mensual repite el mismo mes del año anterior y no ofrece intervalos ni certezas.

## Verificación

Este cambio de experiencia conserva backend y contratos. Pasan 15 tests backend relevantes, 23 frontend y 17 escenarios E2E, lint, TypeScript, build y cuatro contratos import-linter. Los recorridos incluyen axe y tamaños 1280/768/390px; se revisan capturas de Resultados y Dashboard en escritorio y móvil. La validación automatizada no equivale a certificación exhaustiva de accesibilidad.
