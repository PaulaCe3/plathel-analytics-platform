# Fase 7: exportación y demos

## API y formatos

`POST /api/v1/datasets/{dataset_id}/export` requiere stage ready y usa ExportOptions del core, publicado como contrato OpenAPI. Opciones: format (csv/xlsx), scope (clean_data/filtered_data), filters (FilterClause), headers (friendly/original), include_original_columns, include_ignored_columns e include_transformations.

ExporterRegistry resuelve el formato; agregar un exporter no cambia el dispatch del endpoint. ExportSource contiene filas tipadas, encabezados, resumen y TransformationLog reales. No hay cálculos BI en el exporter.

CSV entrega UTF-8 con BOM y CRLF en streaming incremental. Como PresentationSettings aún no existe, usa Settings.default_locale: locales es emplean punto y coma y decimal con coma; el resto emplea coma y punto. XLSX usa openpyxl write_only, genera el ZIP final en BytesIO y lo entrega en bloques de 64 KiB. openpyxl utiliza XML temporal interno para las hojas, que se elimina; no se persiste ningún archivo final ni export en la sesión. Se conserva la limitación de memoria del buffer XLSX, sin introducir infraestructura nueva.

La hoja Datos contiene canonical completo o filtrado. Registro de cambios incluye el TransformationLog auditado, salvo include_transformations=false. Resumen contiene industria, filas exportadas y canonical, moneda, alcance, filtros, mapping, cantidad de transformaciones y generación UTC; no incluye paths ni nombres de archivos fuente.

## Filtros, originales y encabezados

DataEngine.iter_rows proyecta filas completas por lotes y reutiliza QuerySpec y el mismo _apply_filter del Query Engine. No utiliza preview ni muestras. Los filtros son efectivos exclusivamente para filtered_data; clean_data exporta el canonical entero. Una selección vacía genera un archivo válido con encabezados y, en XLSX, resumen de cero filas.

include_original_columns agrega columnas fuente mapeadas; include_ignored_columns agrega las ignoradas/no mapeadas. Se consultan por posición raw (_row_id - 1), sin modificar raw ni volver a incorporar filas eliminadas. Los originales se agregan como columnas separadas, conservando el canonical limpio. Con headers=friendly llevan prefijo Original; con original se resuelven colisiones mediante sufijos deterministas (2), (3), etc. Los custom conservan nombres fuente comprensibles; un campo derivado sin origen inequívoco usa su nombre canónico.

Toda celda textual con prefijo =, +, -, @, TAB, CR o LF se neutraliza con apóstrofo, en encabezados, datos, originales, resumen y auditoría. LF también se protege porque el lector XLSX normaliza CR a LF. Los números negativos tipados conservan su valor. Los valores invalidables permanecen en canonical como ya decidió la limpieza; exportar no agrega transformaciones de datos.

Los errores de formato, stage, filtro/campo, expiración e inicialización del exporter usan AppError/envelope. Los errores de schema se normalizan sin devolver los inputs del usuario. Se valida la consulta y se inicializa el exporter antes de responder; una falla de I/O posterior a iniciar un stream HTTP puede interrumpir la descarga y no puede cambiar el status ya enviado.

## Demos y flujo real

GET /api/v1/demos lista retail_demo, services_demo y hospitality_demo desde demo.json. POST /api/v1/datasets/demo crea una sesión con DatasetService.create y aplica preset_mapping mediante MappingService.save. demo_id identifica datos sintéticos para la UI; ningún cálculo consulta esa metadata.

Los datos limpios sintéticos de backend/demo_data son la única fuente usada por las demos y sus tests. Los fixtures sucios existentes conservan su propósito de regresión y no se copiaron al producto. Retail declara costo total y descuento como importe. Hotelería aporta nights explícito; room_reference es una columna ignorada en su preset porque no es un campo del perfil.

En /bi, Probar demo permite seleccionar rubro y abre Review. Review valida y solicita confirmar la limpieza; luego ofrece Ver dashboard. Review y dashboard indican Modo demo y permiten revisar mapping. Dashboard exporta CSV/XLSX con todas las opciones; la descarga usa Blob y libera Object URLs. Mientras se actualiza el dashboard, Exportar queda deshabilitado; utiliza la misma versión de filtros que produjo los datos visibles.

Las pruebas de demo detectaron y corrigieron la pérdida de insights durante la serialización del DashboardResponse: ahora InsightsResult es un contrato tipado, generado desde OpenAPI. Se habilitó PUT en CORS para los endpoints reales de mapping/cleaning y se expone Content-Disposition para la descarga.

## Verificación y límites de fase

Las integraciones cubren demo → sesión → mapping → validate → cleaning → dashboard → filtros → export y upload propio → mapping → cleaning → dashboard → CSV/XLSX. Los XLSX se reabren con openpyxl; CSV se parsea verificando BOM, locale, encabezados y filas. Se comparan filtros con QuerySpec, se comprueba raw inmutable y ausencia de archivos exportados persistidos. Los tests de frontend ejecutan helpers TypeScript reales con Node, incluyendo respuesta binaria, errores, filtros y Object URLs.

No existe Playwright instalado: la suite completa de navegador queda para Fase 8. No se agregó PDF, ZIP canonical, reportes, handoff, infraestructura ni hardening general. CanonicalManifest no existe; no se introdujo en esta fase.
