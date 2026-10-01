"""Dashboard application service; filters enter every QuerySpec from here."""
from analytics_core.operations import session_operation
from analytics_core.operations import heavy_operation

from datetime import UTC, datetime

from analytics_core.canonical.fields import FieldSpec
from analytics_core.engine.pandas_impl import PandasDataEngine
from analytics_core.errors import AppError
from analytics_core.mapping.models import ColumnDisposition
from analytics_core.mapping.matcher import normalize_name
from analytics_core.sessions.store import DatasetSessionStore
from analytics_core.settings import Settings
from bi.dashboard.builder import DashboardBuilder
from bi.dashboard.filters import option_values
from bi.dashboard.widgets import DashboardRequest, DashboardResponse, FilterOption
from bi.profiles.metrics import build_profile_registry
from bi.profiles import get_profile
from bi.profiles.registry import profile_fields


class DashboardService:
    def __init__(self, settings: Settings):
        self.store = DatasetSessionStore(settings.dataset_storage_path, settings.dataset_ttl_minutes, settings.absolute_session_ttl_minutes)
        self.engine = PandasDataEngine()

    def _ready(self, dataset_id: str):
        session = self.store.get(dataset_id)
        if session.stage != "ready":
            raise AppError(code="STAGE_NOT_READY", http_status=409, message="El dataset debe estar listo antes de generar el dashboard.")
        try:
            profile = get_profile(session.industry_id or "custom")
        except KeyError as exc:
            raise AppError(code="PROFILE_NOT_FOUND", http_status=404, message="El perfil no existe.") from exc
        return session, profile

    def _fields(self, session, profile):
        fields = profile_fields(profile)
        custom_kind = {ColumnDisposition.custom_dimension: "dimension", ColumnDisposition.custom_measure: "measure"}
        column_names = {column.key: column.original_name for column in session.columns}
        used = set()
        for mapping in session.mappings:
            if mapping.disposition == ColumnDisposition.ignored:
                continue
            if mapping.disposition == ColumnDisposition.canonical:
                used.add(mapping.target_field)
                continue
            base = normalize_name(column_names.get(mapping.column_key, mapping.column_key)) or mapping.column_key
            field_id = f"custom__{base}"
            if field_id in used:
                field_id = f"{field_id}__{mapping.column_key}"
            used.add(field_id)
            if field_id in session.canonical_columns:
                kind = custom_kind[mapping.disposition]
                fields.append(FieldSpec(id=field_id, label_key=field_id, kind=kind, dtype="string" if kind == "dimension" else "decimal", scope="custom"))
        return fields

    @session_operation
    @heavy_operation
    def dashboard(self, dataset_id: str, request: DashboardRequest) -> DashboardResponse:
        session, profile = self._ready(dataset_id)
        available = set(session.canonical_columns)
        fields = self._fields(session, profile)
        time_fields = {field.id for field in fields if field.kind == "time" and field.id in available}
        time_field = request.time_field or profile.data.primary_date
        if request.time_field and time_field not in time_fields:
            raise AppError(code="TIME_FIELD_INVALID", http_status=422, message="El campo temporal seleccionado no está disponible.")
        unknown = {clause.field for clause in request.filters} - available
        if unknown:
            raise AppError(code="FILTER_FIELD_INVALID", http_status=422, message="Uno o más filtros usan campos no disponibles.")
        builder = DashboardBuilder(self.engine, build_profile_registry(profile, session.mappings))
        spec, data, filtered, warnings = builder.build(profile=profile, canonical_path=self.store.path(dataset_id, "canonical.parquet"), fields=fields, available=available, filters=request.filters, comparison=request.comparison, time_field=time_field, grain=request.grain, quality=session.quality_summary, row_count=session.canonical_row_count or session.row_count)
        segment_comparison = builder.compare(profile=profile, canonical_path=self.store.path(dataset_id, "canonical.parquet"),
            available=available, fields=fields, filters=request.filters, selection=request.segment_comparison) if request.segment_comparison else None
        return DashboardResponse(spec=spec, data=data, row_count=session.canonical_row_count or session.row_count,
            filtered_row_count=filtered, warnings=warnings, segment_comparison=segment_comparison,
            generated_at=datetime.now(UTC))

    @session_operation
    def filter_options(self, dataset_id: str, field: str, query: str | None, limit: int) -> list[FilterOption]:
        session, profile = self._ready(dataset_id)
        fields = {item.id: item for item in self._fields(session, profile)}
        if field not in session.canonical_columns or field not in fields or fields[field].kind not in {"dimension", "identifier"}:
            raise AppError(code="FILTER_FIELD_INVALID", http_status=422, message="El campo no admite opciones de filtro.")
        return option_values(self.engine, self.store.path(dataset_id, "canonical.parquet"), field, query, limit)
