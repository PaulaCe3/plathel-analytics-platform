"""Build a neutral export source from a real ready session and audited canonical."""
from analytics_core.operations import session_operation
from analytics_core.operations import heavy_operation, stage
from datetime import UTC, datetime
from dataclasses import dataclass
from collections.abc import Iterator
from itertools import chain
import pyarrow.parquet as pq
from analytics_core.engine.pandas_impl import PandasDataEngine
from analytics_core.engine.query import MeasureSpec, QuerySpec
from analytics_core.errors import AppError
from analytics_core.exports import ExportOptions, ExportSource, build_exporter_registry
from analytics_core.exports.security import unique_headers
from analytics_core.mapping.matcher import normalize_name
from analytics_core.mapping.models import ColumnDisposition
from analytics_core.sessions.store import DatasetSessionStore
from bi.profiles import get_profile

LABELS = {"date": "Fecha", "amount": "Importe", "transaction_id": "Operación", "customer_id": "ID cliente", "customer_name": "Cliente", "quantity": "Cantidad", "unit_price": "Precio unitario", "cost": "Costo", "discount": "Descuento", "category": "Categoría", "subcategory": "Subcategoría", "channel": "Canal", "location": "Ubicación", "responsible": "Responsable", "status": "Estado", "currency": "Moneda", "duration_hours": "Horas de servicio", "project": "Proyecto", "booking_date": "Fecha de reserva", "check_in": "Entrada", "check_out": "Salida", "nights": "Noches", "room_type": "Tipo de habitación", "guests": "Huéspedes"}


@dataclass
class PreparedExport:
    chunks: Iterator[bytes]
    content_type: str
    filename: str
    row_count: int
    column_count: int


class ExportService:
    def __init__(self, settings):
        self.settings = settings
        self.store = DatasetSessionStore(settings.dataset_storage_path, settings.dataset_ttl_minutes, settings.absolute_session_ttl_minutes)
        self.engine = PandasDataEngine()
        self.registry = build_exporter_registry()

    @session_operation
    @heavy_operation
    @stage("export")
    def prepare(self, dataset_id: str, options: ExportOptions) -> PreparedExport:
        session = self.store.get(dataset_id)
        if session.stage != "ready":
            raise AppError(code="STAGE_NOT_READY", http_status=409, message="El dataset debe estar listo antes de exportarlo.")
        exporter = self.registry.get(options.format)
        if {clause.field for clause in options.filters} - set(session.canonical_columns):
            raise AppError(code="FILTER_FIELD_INVALID", http_status=422, message="Un filtro usa un campo no disponible.")
        filters = options.filters if options.scope == "filtered_data" else []
        canonical = self.store.path(dataset_id, "canonical.parquet")
        try:
            try:
                count = self.engine.run_query(canonical, QuerySpec(measures=[MeasureSpec(alias="rows", aggregation="count")], filters=filters)).rows[0]["rows"]
            except (TypeError, ValueError) as exc:
                raise AppError(code="EXPORT_FILTER_INVALID", http_status=422, message="Los valores del filtro no son compatibles con el campo.") from exc
            source = self._source(session, options, filters, canonical, int(count))
            chunks = iter(exporter.export(source, options))
            # Trigger initialization before HTTP headers, so failures use AppError.
            first = next(chunks)
            return PreparedExport(self._stream(dataset_id, chain((first,), chunks), options.format, int(count), len(source.headers)), exporter.content_type, f"datos.{exporter.format}", int(count), len(source.headers))
        except AppError:
            raise
        except Exception as exc:
            raise AppError(code="EXPORT_FAILED", http_status=500, message="No se pudo generar la exportación.") from exc

    def _stream(self, dataset_id, chunks, format, rows, columns):
        from contextlib import nullcontext
        from analytics_core.logging import timed
        if format == "xlsx":
            yield from chunks
            return
        with self.store.lock(dataset_id):
            with self.runtime.heavy() if getattr(self, "runtime", None) else nullcontext():
                with timed("export") as counts:
                    counts.update(rows=rows, columns=columns)
                    yield from chunks

    def _source(self, session, options, filters, canonical, count):
        profile = get_profile(session.industry_id or "custom")
        terms = profile.data.terminology.get(self.settings.default_locale.split("-")[0], {})
        column_names = {item.key: item.original_name for item in session.columns}
        original_by_field = {}
        used = set()
        for mapping in session.mappings:
            if mapping.disposition == ColumnDisposition.ignored:
                continue
            if mapping.target_field:
                target = mapping.target_field
            else:
                base = normalize_name(column_names.get(mapping.column_key, mapping.column_key)) or mapping.column_key
                target = f"custom__{base}"
                if target in used:
                    target += f"__{mapping.column_key}"
            used.add(target)
            original_by_field[target] = column_names.get(mapping.column_key, target)
        visible = [field for field in session.canonical_columns if not field.startswith("_")]
        headers = []
        for field in visible:
            fallback = original_by_field.get(field, field.removeprefix("custom__").replace("_", " "))
            headers.append(original_by_field.get(field, fallback) if options.headers == "original" else terms.get(field, LABELS.get(field, fallback)))
        mapped = {item.column_key for item in session.mappings if item.disposition != ColumnDisposition.ignored}
        original_keys = [item.key for item in session.columns if (item.key in mapped and options.include_original_columns) or (item.key not in mapped and options.include_ignored_columns)]
        headers += [("Original · " if options.headers == "friendly" else "") + column_names[key] for key in original_keys]
        raw = pq.read_table(self.store.path(session.dataset_id, "raw.parquet"), columns=original_keys) if original_keys else None
        def rows():
            query = QuerySpec(measures=[], filters=filters)
            for row in self.engine.iter_rows(canonical, query, ["_row_id", *visible]):
                values = [row[field] for field in visible]
                if raw is not None:
                    index = int(row["_row_id"]) - 1
                    if not 0 <= index < raw.num_rows:
                        raise ValueError("Invalid canonical row identity")
                    values.extend(raw[key][index].as_py() for key in original_keys)
                yield values
        currency = None
        if "currency" in visible:
            from analytics_core.engine.query import GroupBy
            currencies = self.engine.run_query(canonical, QuerySpec(measures=[MeasureSpec(alias="rows", aggregation="count")], group_by=[GroupBy(field="currency")], filters=filters)).rows
            values = {row["currency"] for row in currencies if row["currency"] not in (None, "")}
            currency = next(iter(values)) if len(values) == 1 else "Múltiples monedas" if values else None
        summary = {"Industria": profile.name, "Filas exportadas": count, "Filas canonical": session.canonical_row_count, "Moneda": currency or "No informada", "Alcance": "Datos filtrados" if options.scope == "filtered_data" else "Datos limpios", "Filtros": [clause.model_dump(mode="json") for clause in filters], "Mapping": [{"columna": column_names.get(item.column_key, item.column_key), "campo": item.target_field or item.disposition.value, "opciones": item.options} for item in session.mappings], "Transformaciones": len(session.transformation_log.transformations), "Generado (UTC)": datetime.now(UTC).isoformat()}
        return ExportSource(unique_headers(headers), rows, summary, session.transformation_log, self.settings.default_locale)
