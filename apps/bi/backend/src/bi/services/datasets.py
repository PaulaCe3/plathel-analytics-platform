"""Application orchestration for raw dataset ingestion."""
from analytics_core.operations import session_operation

from pathlib import Path
from analytics_core.operations import heavy_operation, stage
from typing import BinaryIO

from analytics_core.engine.pandas_impl import PandasDataEngine
from analytics_core.errors import AppError
from analytics_core.ingestion.models import SourceSettings
from analytics_core.mapping.models import ColumnDisposition, ColumnMapping
from analytics_core.mapping.matcher import suggest_mappings
from analytics_core.sessions.models import DatasetSession, FileMetadata
from analytics_core.sessions.store import DatasetSessionStore
from analytics_core.settings import Settings
from analytics_core.sources import UploadSource
from bi.profiles import get_profile, list_profiles
from bi.profiles.registry import profile_fields


class DatasetService:
    def __init__(self, settings: Settings, runtime=None, client_ip="local") -> None:
        self.runtime, self.client_ip = runtime, client_ip
        self.settings = settings
        self.store = DatasetSessionStore(settings.dataset_storage_path, settings.dataset_ttl_minutes, settings.absolute_session_ttl_minutes)
        self.engine = PandasDataEngine(settings.profile_sample_rows)
        self.upload_source = UploadSource()

    def create(self, stream: BinaryIO, filename: str, industry_id: str | None) -> DatasetSession:
        if self.runtime:
            with self.runtime.creation(self.client_ip) as committed:
                session = self._create(stream, filename, industry_id)
                committed.append(session.dataset_id)
                return session
        return self._create(stream, filename, industry_id)

    def _create(self, stream: BinaryIO, filename: str, industry_id: str | None) -> DatasetSession:
        session = self.store.create(industry_id)
        source_path = self.store.path(session.dataset_id, "source.bin")
        try:
            extension, size = self.upload_source.save(
                stream,
                filename,
                source_path,
                allowed_extensions=self.settings.allowed_extensions,
                max_bytes=self.settings.max_file_mb * 1024 * 1024,
                max_zip_entries=self.settings.max_zip_entries,
                max_zip_expanded_bytes=self.settings.max_zip_expanded_mb * 1024 * 1024,
                max_zip_ratio=self.settings.max_zip_ratio,
            )
            session.file = FileMetadata(original_name=Path(filename).name[:100], extension=extension, size_bytes=size)
            self.store.save(session)
            return self._parse(session, source_path, extension, SourceSettings())
        except Exception as exc:
            try:
                self.store.delete(session.dataset_id)
            except AppError:
                pass
            if isinstance(exc, OSError):
                raise AppError(code="STORAGE_UNAVAILABLE", http_status=503, message="No se pudo guardar el archivo temporal.") from exc
            raise

    @heavy_operation
    def _parse(self, session: DatasetSession, source_path: Path, extension: str, source_settings: SourceSettings) -> DatasetSession:
        result = self.engine.parse_to_parquet(
            source_path,
            extension,
            self.store.path(session.dataset_id, "raw.parquet"),
            source_settings,
            max_rows=self.settings.max_rows,
            max_columns=self.settings.max_columns,
        )
        session.stage = "parsed"
        session.mappings = []
        self._invalidate_canonical(session)
        session.parsing_status = "complete"
        session.source_settings = result.source_settings
        session.selected_sheet = result.selected_sheet
        session.available_sheets = result.available_sheets
        session.row_count = result.row_count
        session.column_count = result.column_count
        session.columns = result.columns
        session.warnings = result.warnings
        self.store.save(session)
        if extension == ".csv":
            source_path.unlink(missing_ok=True)
        return session

    @session_operation
    def get(self, dataset_id: str) -> DatasetSession:
        return self.store.get(dataset_id)

    @session_operation
    def preview(self, dataset_id: str, rows: int) -> tuple[DatasetSession, list[dict[str, str | None]]]:
        session = self.store.get(dataset_id)
        if session.stage not in {"parsed", "mapped"}:
            raise AppError(code="STAGE_NOT_READY", http_status=409, message="El dataset todavía no está listo.")
        return session, self.engine.preview(self.store.path(dataset_id, "raw.parquet"), rows)

    @session_operation
    def update_source(self, dataset_id: str, changes: SourceSettings) -> DatasetSession:
        session = self.store.get(dataset_id)
        if session.stage != "parsed" or not session.file or session.file.extension != ".xlsx":
            raise AppError(code="STAGE_NOT_READY", http_status=409, message="Solo se puede cambiar la hoja de un XLSX.")
        source_path = self.store.path(dataset_id, "source.bin")
        if not source_path.is_file():
            raise AppError(code="STAGE_NOT_READY", http_status=409, message="El archivo fuente ya no está disponible.")
        updates = changes.model_dump(exclude_unset=True, exclude_none=True)
        if "sheet" in updates and "header_row" not in updates:
            updates["header_row"] = None
        merged = session.source_settings.model_copy(update=updates)
        return self._parse(session, source_path, ".xlsx", merged)

    @session_operation
    def delete(self, dataset_id: str) -> None:
        self.store.delete(dataset_id)

    @session_operation
    def autopilot(self, dataset_id: str) -> dict:
        from bi.services.mapping import MappingService
        from bi.services.prepare import PrepareService

        session = self.store.get(dataset_id)
        if session.stage == "ready":
            return self._autopilot_result(session, "ready", "Tus datos ya están listos.", "results")
        if session.stage != "parsed":
            return self._autopilot_result(session, "intervention_required", "No pudimos preparar automáticamente este archivo desde su estado actual.", "mapping")
        profile, mappings, reason = self._autopilot_mapping(session)
        if mappings is None:
            return self._autopilot_result(session, "intervention_required", reason, "mapping", profile.id)
        mapping = MappingService(self.settings)
        mapping.save(dataset_id, profile.id, mappings)
        prepare = PrepareService(self.settings)
        prepare.runtime = self.runtime
        session, validation, _quality = prepare.validate(dataset_id)
        if not validation.valid:
            return self._autopilot_result(session, "intervention_required", "No pudimos interpretar con seguridad algunos valores imprescindibles. Revisá únicamente las observaciones señaladas.", "review", profile.id)
        safe = [action for action in (session.cleaning_plan.actions if session.cleaning_plan else []) if action.selected and not action.destructive]
        session, _quality = prepare.clean(dataset_id, safe)
        return self._autopilot_result(session, "ready", "Tus datos fueron preparados automáticamente sin eliminar filas ni inventar valores.", "results", profile.id)

    def _autopilot_mapping(self, session: DatasetSession):
        evaluated = []
        for profile in list_profiles():
            fields = profile_fields(profile)
            suggestions = suggest_mappings(session.columns, fields, profile.data.aliases)
            winners = {}
            tied_required = set()
            required = {rule.field_id for rule in profile.data.fields if rule.level == "required"}
            for suggestion in suggestions:
                if not suggestion.candidates or suggestion.candidates[0].confidence != "high":
                    continue
                candidate = suggestion.candidates[0]
                previous = winners.get(candidate.field_id)
                if previous and abs(previous[1] - candidate.score) < 0.02:
                    if candidate.field_id in required:
                        tied_required.add(candidate.field_id)
                    continue
                if previous is None or candidate.score > previous[1]:
                    winners[candidate.field_id] = (suggestion.column_key, candidate.score)
            mapped = set(winners)
            time_fields = {field.id for field in fields if field.kind == "time"}
            measure_fields = {field.id for field in fields if field.kind == "measure"}
            viable = required <= mapped and bool(mapped & time_fields) and bool(mapped & measure_fields) and not tied_required
            score = sum(value[1] for value in winners.values())
            evaluated.append((profile, winners, suggestions, viable, score))
        custom = next(item for item in evaluated if item[0].id == "custom")
        viable_specific = [item for item in evaluated if item[0].id != "custom" and item[3]]
        viable_specific.sort(key=lambda item: (-item[4], item[0].id))
        selected = custom
        if viable_specific:
            best = viable_specific[0]
            runner_score = viable_specific[1][4] if len(viable_specific) > 1 else custom[4]
            if best[4] >= custom[4] + 0.5 and best[4] >= runner_score + 0.25:
                selected = best
        profile, winners, suggestions, viable, _score = selected
        if not viable:
            return profile, None, "No pudimos identificar con seguridad una fecha y un valor numérico necesarios para analizar el archivo."
        winner_by_column = {column: field for field, (column, _score) in winners.items()}
        mappings = []
        custom_dimensions = custom_measures = 0
        for suggestion in suggestions:
            target = winner_by_column.get(suggestion.column_key)
            if target:
                mappings.append(ColumnMapping(column_key=suggestion.column_key, target_field=target, disposition=ColumnDisposition.canonical))
            elif suggestion.suggested_disposition == ColumnDisposition.custom_dimension and custom_dimensions < self.settings.max_custom_dimensions:
                mappings.append(ColumnMapping(column_key=suggestion.column_key, disposition=ColumnDisposition.custom_dimension)); custom_dimensions += 1
            elif suggestion.suggested_disposition == ColumnDisposition.custom_measure and custom_measures < self.settings.max_custom_measures:
                mappings.append(ColumnMapping(column_key=suggestion.column_key, disposition=ColumnDisposition.custom_measure)); custom_measures += 1
            else:
                mappings.append(ColumnMapping(column_key=suggestion.column_key, disposition=ColumnDisposition.ignored))
        return profile, mappings, ""

    @staticmethod
    def _autopilot_result(session, status, explanation, destination, profile_id=None):
        return {"dataset_id": session.dataset_id, "status": status, "stage": session.stage, "profile_id": profile_id or session.industry_id or "custom", "explanation": explanation, "destination": destination}

    @session_operation
    def change_industry(self, dataset_id: str, industry_id: str) -> DatasetSession:
        try:
            get_profile(industry_id)
        except KeyError as exc:
            raise AppError(code="PROFILE_NOT_FOUND", http_status=404, message="El perfil de industria no existe.") from exc
        session = self.store.get(dataset_id)
        session.industry_id = industry_id
        session.mappings = []
        session.stage = "parsed"
        self._invalidate_canonical(session)
        self.store.save(session)
        return session

    def _invalidate_canonical(self, session: DatasetSession) -> None:
        self.store.path(session.dataset_id, "canonical.parquet").unlink(missing_ok=True)
        session.has_canonical = False
        session.canonical_row_count = None
        session.canonical_columns = []
        session.validation_status = None
        session.validation_report = None
        session.parse_reports = []
        session.quality_summary = None
        session.cleaning_plan = None
        session.cleaning_actions = []
        session.cleaning_confirmed = False
        session.transformation_log.transformations = []
