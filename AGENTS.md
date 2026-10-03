# AGENTS.md

## Regla principal
Usar el mínimo contexto necesario para completar cada tarea.

No explorar todo el repositorio por defecto.
No leer documentación que no sea relevante para la tarea.
No releer archivos ya comprendidos salvo que hayan cambiado.

## Contexto

- Contexto general → docs/CONTEXT.md
- Arquitectura → docs/ARCHITECTURE.md
- Diseño/UI → docs/DESIGN_SYSTEM.md
- Decisiones previas → docs/DECISIONS.md

Consultar únicamente los documentos necesarios para la tarea actual.

## Código

Antes de modificar:
1. Identificar los archivos directamente relacionados.
2. Leer únicamente esos archivos y sus dependencias necesarias.
3. Evitar búsquedas globales salvo necesidad.

## Tests

Ejecutar primero los tests relacionados con el cambio.

No ejecutar toda la suite salvo:
- cambios arquitectónicos;
- cambios compartidos;
- riesgo de regresión;
- petición explícita.

## Finalización

Informar únicamente:
- archivos modificados;
- cambio realizado;
- tests ejecutados;
- problemas pendientes.
