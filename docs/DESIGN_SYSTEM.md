# PLATHEL — sistema visual

Alcance: Análisis y Predicciones. Wordmark textual temporal: no hay isotipo oficial en el repositorio. UI compartida en `packages/ui`; backend descriptivo y forecasting independientes. La ingestión, preparación, exportaciones, sesiones y seguridad existentes se conservan.

## Auditoría y decisiones

- Marca previa, colores verdes/azules y superficies inconsistentes → PLATHEL, descriptor DATA · AI · AUTOMATION y tokens minerales.
- Selectores de columnas, claves internas y scores dominantes → resumen de identificadas; ambiguas visibles; todas las selecciones disponibles en Ver todas. La propuesta y el payload existentes no cambian. La clasificación visual usa la confianza entregada por backend y los conflictos.
- Revisión técnica con acciones cero/observaciones abiertas → ajustes recomendados explicados, acciones con impacto cero omitidas y cambios realizados accesibles. Eliminaciones nunca preseleccionadas; requieren diálogo explícito antes de llamar al endpoint.
- Todos los widgets simultáneos → Resultados presenta una lectura narrativa con hasta dos cifras relevantes, tres hallazgos editoriales y una predicción. Dashboard concentra hasta cinco KPIs, evolución, hallazgos adicionales y un único desglose seleccionable. Las conclusiones locales no se repiten en Hallazgos. Resto de métricas/detalles disponibles. Las interpretaciones reutilizan reglas determinísticas del backend con los mismos filtros. Las barras compatibles y sus botones tabulares comparten FilterClause con los controles; chips permiten quitar filtros y Limpiar restablece el contexto. No se calculan conclusiones en frontend.
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
| Moss | #4F5948 | Datos, selección y acentos positivos |
| Wine | #6B3037 | Error, atención y destrucción |

Mineral/Mar ocupa la mayor parte de la interfaz. Moss y Wine son microacentos funcionales y siempre se acompañan con texto; las comparaciones sin semántica segura usan Graphite. Space Grotesk para títulos e Inter para cuerpo, alojadas localmente con licencias OFL; títulos 30–44px internos/38–64px home; cuerpo 14–16px. Espaciado base 24px, controles mínimo 44px, radios 6px. Sin sombras decorativas ni gradientes.

## Primitives y patrones

`packages/ui/src/primitives.tsx` (reexportado por BI): Button (primary/secondary/ghost/danger, busy/disabled), Card (sección con divisor), Input, Select, Status, Toast (info/success/error), SectionHeader, EmptyState, ErrorState con retry, LoadingState y Dialog.

`packages/ui/src/product-header.tsx`: marca y navegación Demo → Resultados → Dashboard; `product-navigation.tsx`: adaptación y Stepper. Columnas y preparación pertenecen al primer momento; pasos futuros no son enlaces que permitan saltar validaciones. Los completados/actuales llevan texto accesible, sin depender del color.

Sesión y privacidad se agrupan bajo Opciones. La etiqueta DEMO es discreta; revisar datos queda en Opciones. Filtros compactos, chips solo cuando están activos y Exportar junto al encabezado. Sobre estos datos permanece cerrado. Divisores limitados a cambios de jerarquía; controles interactivos usan cursor, foco, hover y selección distinguible por borde además del color.

Dialog usa HTML dialog/showModal: foco modal, tabulación contenida, Escape, botón Cerrar y retorno de foco al disparador. Está etiquetado por título. Export y confirmación de transformaciones destructivas reutilizan el mismo patrón. Loading/error/toasts usan status/alert y aria-live; botones ocupados deshabilitados. Siempre usar label o aria-label en Input/Select.

DashboardRenderer y estados de widgets reutilizan las mismas primitives; no hay un segundo juego de EmptyState/ErrorState. ECharts mantiene aria/decal, ResizeObserver y alternativa de tabla de los mismos puntos. Comparaciones muestran flecha, signo, porcentaje y texto. Los gráficos usan Moss como acento y la escala mineral para contexto. Forecast distingue historial oscuro, futuro Moss discontinuo y rango Platinum; no dibuja intervalos inexistentes.

Responsive: shell máximo 1280px; lectura/preparación máximo 960px; padding 40/24/20px; columnas y filtros se apilan en móvil. Tabla con scroll local. KPIs en una fila flexible en desktop, dos columnas en tablet y una en móvil. Todos los controles conservan foco visible; spinner y scroll respetan reduced-motion.

Preparación distingue Ajustes recomendados, Necesita tu atención y Opciones avanzadas con impacto real. Una única acción continúa; los ajustes seguros se pueden desmarcar. Eliminaciones se eligen con radios conservar/eliminar y confirmación posterior. Toolbar con período primero, controles de 44px y chevrons discretos; rangos rápidos se anclan a la última fecha disponible del dataset. Personalizado muestra desde/hasta; chips y Limpiar comparten estado. Gráficos con ejes suaves, barras horizontales y sin leyenda redundante de una sola serie.

## Predicciones

Nota de vigencia: la descripción de base mensual sin intervalos que sigue corresponde al diseño inicial. F5 ya implementó selección de modelos y rangos empíricos del 80 % cuando hay evidencia suficiente; consultar [estado actual — F5](knowledge/CURRENT_STATE.md) antes de cambiar forecast. La verificación al final es histórica, no una comprobación de la sesión actual.

Comparte cabecera, estilos, fuentes, controles y EChartsBase. Resultados integra «Qué podría pasar después» y crea automáticamente una estimación si los datos son compatibles; no muestra selector de variable, horizonte ni botón de creación. La vista standalone conserva esos controles. Los resultados muestran período observado, horizonte, tabla alternativa y una limitación breve; evaluación histórica y metodología quedan dentro de ¿Cómo se calculó?. Cuando no hay predicción, una línea discreta y Ver por qué reemplazan la sección amplia.

## Verificación

Este cambio conserva backend y contratos. Pasan 9 tests backend relevantes, 27 frontend y 16 escenarios E2E distintos; ocho recorridos afectados se comprueban sobre el build final. Lint, TypeScript, build y cuatro contratos import-linter pasan. Los recorridos incluyen axe y tamaños 1280/768/390px; se revisan capturas de Datos, preparación, Resultados y Dashboard en escritorio y móvil. La validación automatizada no equivale a certificación exhaustiva de accesibilidad.


