"""Mapping orchestration between generic core and profile registry."""

from analytics_core.errors import AppError
from analytics_core.mapping.matcher import suggest_mappings
from analytics_core.mapping.models import ColumnMapping
from analytics_core.mapping.validation import validate_mapping
from analytics_core.sessions.models import DatasetSession
from analytics_core.sessions.store import DatasetSessionStore
from analytics_core.settings import Settings
from bi.profiles import get_profile
from bi.profiles.registry import profile_fields


class MappingService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.store = DatasetSessionStore(settings.dataset_storage_path, settings.dataset_ttl_minutes)

    def _profile(self, profile_id: str):
        try:
            return get_profile(profile_id)
        except KeyError as exc:
            raise AppError(code="PROFILE_NOT_FOUND", http_status=404, message="El perfil de industria no existe.") from exc

    def view(self, dataset_id: str):
        session = self.store.get(dataset_id)
        profile = self._profile(session.industry_id or "custom")
        fields = profile_fields(profile)
        suggestions = suggest_mappings(session.columns, fields, profile.data.aliases)
        required = {rule.field_id for rule in profile.data.fields if rule.level == "required"}
        conflicts = validate_mapping(session.mappings, session.columns, fields, required, max_custom_dimensions=self.settings.max_custom_dimensions, max_custom_measures=self.settings.max_custom_measures) if session.mappings else []
        mapped_columns = {mapping.column_key for mapping in session.mappings}
        return session, profile, fields, suggestions, conflicts, [column.key for column in session.columns if column.key not in mapped_columns]

    def save(self, dataset_id: str, profile_id: str, mappings: list[ColumnMapping]) -> DatasetSession:
        session = self.store.get(dataset_id)
        profile = self._profile(profile_id)
        fields = profile_fields(profile)
        required = {rule.field_id for rule in profile.data.fields if rule.level == "required"}
        conflicts = validate_mapping(mappings, session.columns, fields, required, max_custom_dimensions=self.settings.max_custom_dimensions, max_custom_measures=self.settings.max_custom_measures)
        blocking = [conflict for conflict in conflicts if conflict.severity == "error"]
        if blocking:
            raise AppError(code="MAPPING_INVALID", http_status=422, message="El mapping contiene conflictos bloqueantes.", details=[conflict.model_dump() for conflict in blocking])
        session.industry_id = profile_id
        session.mappings = mappings
        session.stage = "mapped"
        self.store.save(session)
        return session
