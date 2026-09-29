"""Public profile queries."""

from bi.profiles import get_profile, list_profiles
from analytics_core.errors import AppError


class ProfileService:
    def list(self):
        return list_profiles()

    def get(self, profile_id: str):
        try:
            return get_profile(profile_id)
        except KeyError as exc:
            raise AppError(code="PROFILE_NOT_FOUND", http_status=404, message="El perfil de industria no existe.") from exc
