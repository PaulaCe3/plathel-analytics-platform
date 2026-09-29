"""Canonical preparation, validation, quality and confirmed cleaning."""

from analytics_core.canonical.derived import UNIVERSAL_DERIVED_RULES
from analytics_core.cleaning.actions import validate_action_ids
from analytics_core.cleaning.models import CleaningActionSpec, TransformationLog
from analytics_core.engine.pandas_impl import PandasDataEngine
from analytics_core.errors import AppError
from analytics_core.quality.models import DataQualityReport
from analytics_core.sessions.models import DatasetSession
from analytics_core.sessions.store import DatasetSessionStore
from analytics_core.settings import Settings
from analytics_core.validation.models import Issue, ValidationReport, validation_report
from bi.profiles import get_profile
from bi.profiles.registry import profile_fields


class PrepareService:
    def __init__(self, settings: Settings) -> None:
        self.store = DatasetSessionStore(settings.dataset_storage_path, settings.dataset_ttl_minutes)
        self.engine = PandasDataEngine()

    def _context(self, dataset_id: str) -> tuple[DatasetSession, object, list]:
        session = self.store.get(dataset_id)
        try:
            profile = get_profile(session.industry_id or "custom")
        except KeyError as exc:
            raise AppError(code="PROFILE_NOT_FOUND", http_status=404, message="El perfil de industria no existe.") from exc
        return session, profile, profile_fields(profile)

    def _build(self, session: DatasetSession, profile, fields: list, actions: list[CleaningActionSpec]):
        try:
            validate_action_ids(actions)
        except ValueError as exc:
            raise AppError(code="CLEANING_ACTION_INVALID", http_status=422, message="La lista de acciones de limpieza no es válida.") from exc
        result = self.engine.build_canonical(
            self.store.path(session.dataset_id, "raw.parquet"),
            self.store.path(session.dataset_id, "canonical.parquet"),
            session.mappings,
            fields,
            {column.key: column.original_name for column in session.columns},
            session.source_settings,
            list(UNIVERSAL_DERIVED_RULES),
            actions,
        )
        quality = self.engine.inspect_quality(self.store.path(session.dataset_id, "canonical.parquet"), result.parse_reports, list(profile.data.checks))
        return result, quality

    def validate(self, dataset_id: str) -> tuple[DatasetSession, ValidationReport, DataQualityReport]:
        session, profile, fields = self._context(dataset_id)
        if session.stage != "mapped":
            raise AppError(code="STAGE_NOT_READY", http_status=409, message="El dataset debe estar mapeado antes de validarlo.")
        result, quality = self._build(session, profile, fields, [])
        issues = self._validation_issues(session, profile, result.parse_reports, set(result.columns))
        report = validation_report(issues, result.parse_reports)
        plan = self.engine.create_cleaning_plan(self.store.path(dataset_id, "canonical.parquet"), result.parse_reports, quality)
        session.has_canonical = True
        session.canonical_row_count = result.row_count
        session.canonical_columns = result.columns
        session.parse_reports = result.parse_reports
        session.validation_report = report
        session.validation_status = "valid" if report.valid else "invalid"
        session.quality_summary = quality.summary
        session.cleaning_plan = plan
        session.cleaning_actions = []
        session.cleaning_confirmed = False
        session.transformation_log = TransformationLog(transformations=result.transformations)
        session.stage = "validated"
        self.store.save(session)
        return session, report, quality

    def clean(self, dataset_id: str, actions: list[CleaningActionSpec]) -> tuple[DatasetSession, DataQualityReport]:
        session, profile, fields = self._context(dataset_id)
        if session.stage not in {"validated", "ready"}:
            raise AppError(code="CLEANING_NOT_ALLOWED", http_status=409, message="Primero debés validar el dataset.")
        if session.validation_report and not session.validation_report.valid:
            raise AppError(code="VALIDATION_FAILED", http_status=409, message="Resolvé los errores de validación antes de confirmar la limpieza.")
        normalized = [action.model_copy(update={"selected": True}) for action in actions]
        result, quality = self._build(session, profile, fields, normalized)
        issues = self._validation_issues(session, profile, result.parse_reports, set(result.columns))
        report = validation_report(issues, result.parse_reports)
        session.has_canonical = True
        session.canonical_row_count = result.row_count
        session.canonical_columns = result.columns
        session.parse_reports = result.parse_reports
        session.validation_report = report
        session.validation_status = "valid" if report.valid else "invalid"
        session.quality_summary = quality.summary
        session.cleaning_actions = normalized
        session.cleaning_confirmed = True
        session.transformation_log = TransformationLog(transformations=result.transformations)
        session.stage = "ready"
        self.store.save(session)
        return session, quality

    def transformations(self, dataset_id: str) -> TransformationLog:
        return self.store.get(dataset_id).transformation_log

    @staticmethod
    def _validation_issues(session: DatasetSession, profile, reports, available: set[str]) -> list[Issue]:
        required = {rule.field_id for rule in profile.data.fields if rule.level == "required"}
        issues = [Issue(id=f"required:{field}", code="REQUIRED_FIELD_MISSING", scope="field", severity="error", message="Falta un campo requerido.", field_id=field) for field in sorted(required - available)]
        for report in reports:
            if report.invalid_rows:
                severity = "error" if report.invalid_ratio > 0.5 and report.parse_type in {"date", "datetime", "decimal", "integer"} else "warning"
                issues.append(Issue(id=f"parse:{report.field_id}", code="PARSEABILITY_LOW" if severity == "error" else "PARSE_VALUES_INVALID", scope="field", severity=severity, message="Algunos valores no pudieron convertirse; las filas fueron conservadas.", field_id=report.field_id, column_key=report.source_column_key, count=report.invalid_rows, ratio=report.invalid_ratio, sample_row_ids=report.sample_row_ids))
        return issues
