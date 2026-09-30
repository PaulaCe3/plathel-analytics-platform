# PLATHEL — sistema visual BI

Alcance: presentación de Fases 0–8. Sin cambios en backend, contratos, lógica de columnas, cálculos, reglas de hallazgos, exports, sesiones o seguridad. Wordmark textual temporal: no hay isotipo oficial en el repositorio. No se añadieron fuentes, dependencias, servicios ni funcionalidades analíticas.

## Auditoría y decisiones

- Marca previa, colores verdes/azules y superficies inconsistentes → PLATHEL, descriptor DATA · AI · AUTOMATION y tokens minerales.
- Selectores de columnas, claves internas y scores dominantes → resumen de identificadas; ambiguas visibles; todas las selecciones disponibles en Ver todas. La propuesta y el payload existentes no cambian. La clasificación visual usa la confianza entregada por backend y los conflictos.
- Revisión técnica con acciones cero/observaciones abiertas → mejoras relevantes, observaciones colapsadas y cambios realizados accesibles. Eliminaciones nunca preseleccionadas; requieren diálogo explícito antes de llamar al endpoint.
- Todos los widgets simultáneos → hasta seis KPIs según el orden del backend, una evolución, hasta tres hallazgos y un desglose seleccionable. Resto de métricas/detalles disponibles. No se recalculan ni se muestrean valores.
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

Estados funcionales sobrios: rojo para error, ocre para advertencia, verde para éxito; siempre acompañados de texto. Arial/Helvetica local; títulos 30–44px internos/38–64px home; cuerpo 14–16px. Espaciado base 24px, controles mínimo 44px, radios 6px. Sin sombras decorativas ni gradientes.

## Primitives y patrones

`components/ui/primitives.tsx`: Button (primary/secondary/ghost, busy/disabled), Card (sección con divisor), Input, Select, Status, Toast (info/success/error), SectionHeader, EmptyState, ErrorState con retry, LoadingState y Dialog.

`product-navigation.tsx`: ProductHeader y Stepper. Rutas internas: Tus datos → Columnas → Preparación → Análisis; pasos futuros no son enlaces que permitan saltar validaciones. Los completados/actuales llevan texto accesible, sin depender del color.

Dialog usa HTML dialog/showModal: foco modal, tabulación contenida, Escape, botón Cerrar y retorno de foco al disparador. Está etiquetado por título. Export y confirmación de transformaciones destructivas reutilizan el mismo patrón. Loading/error/toasts usan status/alert y aria-live; botones ocupados deshabilitados. Siempre usar label o aria-label en Input/Select.

DashboardRenderer y estados de widgets reutilizan las mismas primitives; no hay un segundo juego de EmptyState/ErrorState. ECharts mantiene aria/decal, ResizeObserver y alternativa de tabla de los mismos puntos. Comparaciones muestran flecha, signo, porcentaje y texto. Los gráficos usan la paleta PLATHEL.

Responsive: shell máximo 1280px, padding 40/24/20px; columnas y filtros se apilan en móvil. Tabla con scroll local. Grid de KPIs mantiene span 12 móvil, 6 tablet y span definido por backend en desktop. Todos los controles conservan foco visible; spinner y scroll respetan reduced-motion.

## Verificación

22 tests Node pasan. Los 15 escenarios Playwright/axe pasan entre la ejecución inicial (10) y la repetición de los cinco afectados después de corregir el contraste del aviso de privacidad. Incluyen archivos propios de tres industrias, filtros, exportaciones, errores, sesión, columnas ambiguas, confirmación destructiva con Escape/retorno de foco, y tamaños 1280/768/390px. Build y los dos contratos import-linter pasan.

La revisión visual manual alcanzó home en desktop/tablet/móvil y columnas en móvil. El navegador integrado bloqueó el acceso al retomar; no se declara completa la inspección visual manual de las cuatro rutas. Los tests automáticos no constituyen una certificación exhaustiva de accesibilidad.
