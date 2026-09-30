# PLATHEL — sistema visual

Alcance: Análisis y Predicciones. Wordmark textual temporal: no hay isotipo oficial en el repositorio. UI compartida en `packages/ui`; backend descriptivo y forecasting independientes. La ingestión, preparación, exportaciones, sesiones y seguridad existentes se conservan.

## Auditoría y decisiones

- Marca previa, colores verdes/azules y superficies inconsistentes → PLATHEL, descriptor DATA · AI · AUTOMATION y tokens minerales.
- Selectores de columnas, claves internas y scores dominantes → resumen de identificadas; ambiguas visibles; todas las selecciones disponibles en Ver todas. La propuesta y el payload existentes no cambian. La clasificación visual usa la confianza entregada por backend y los conflictos.
- Revisión técnica con acciones cero/observaciones abiertas → mejoras relevantes, observaciones colapsadas y cambios realizados accesibles. Eliminaciones nunca preseleccionadas; requieren diálogo explícito antes de llamar al endpoint.
- Todos los widgets simultáneos → hasta seis KPIs según el orden del backend, hasta cuatro gráficos clave seleccionados por backend, hasta tres hallazgos y un desglose seleccionable colapsado. Resto de métricas/detalles disponibles. Las interpretaciones reutilizan reglas determinísticas del backend con los mismos filtros. No se calculan conclusiones en frontend.
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

`packages/ui/src/product-header.tsx`: navegación Análisis / Predicciones; `product-navigation.tsx`: adaptación y Stepper. Rutas internas: Tus datos → Columnas → Preparación → Análisis; pasos futuros no son enlaces que permitan saltar validaciones. Los completados/actuales llevan texto accesible, sin depender del color.

Dialog usa HTML dialog/showModal: foco modal, tabulación contenida, Escape, botón Cerrar y retorno de foco al disparador. Está etiquetado por título. Export y confirmación de transformaciones destructivas reutilizan el mismo patrón. Loading/error/toasts usan status/alert y aria-live; botones ocupados deshabilitados. Siempre usar label o aria-label en Input/Select.

DashboardRenderer y estados de widgets reutilizan las mismas primitives; no hay un segundo juego de EmptyState/ErrorState. ECharts mantiene aria/decal, ResizeObserver y alternativa de tabla de los mismos puntos. Comparaciones muestran flecha, signo, porcentaje y texto. Los gráficos usan la paleta PLATHEL.

Responsive: shell máximo 1280px, padding 40/24/20px; columnas y filtros se apilan en móvil. Tabla con scroll local. Grid de KPIs mantiene span 12 móvil, 6 tablet y span definido por backend en desktop. Todos los controles conservan foco visible; spinner y scroll respetan reduced-motion.

## Predicciones

Comparte cabecera, estilos, fuentes, controles y EChartsBase. Comienza con «¿Qué querés predecir?», ofrece solo valores compatibles y conserva la sesión preparada mediante enlaces. Los resultados muestran período observado, horizonte, tabla alternativa, evaluación histórica y límites; el detalle del modelo queda colapsado. La base mensual repite el mismo mes del año anterior y no ofrece intervalos ni certezas.

## Verificación

La validación actual incluye los contratos de separación de productos, tests backend de disponibilidad/evaluación/sesiones/raw inmutable y recorridos E2E de Análisis y Predicciones con axe y tamaños 1280/768/390px. La revisión visual manual previa quedó parcial por un bloqueo del navegador integrado; no se declara una certificación exhaustiva de accesibilidad.

Resultado final: 191 tests backend, 23 tests frontend y 17 escenarios E2E aprobados; los tres recorridos críticos se repitieron sobre el build final. Lint, TypeScript, build, cuatro contratos import-linter y git diff --check pasan. Los contratos generados coinciden con OpenAPI de la composición final.
