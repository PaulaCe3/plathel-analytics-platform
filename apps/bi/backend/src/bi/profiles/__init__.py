"""Built-in data-only profile registration."""

from bi.profiles.custom.profile import PROFILE as CUSTOM
from bi.profiles.hospitality.profile import PROFILE as HOSPITALITY
from bi.profiles.registry import get_profile, list_profiles, register_profile
from bi.profiles.retail_ecommerce.profile import PROFILE as RETAIL
from bi.profiles.services.profile import PROFILE as SERVICES

for _profile in (CUSTOM, RETAIL, SERVICES, HOSPITALITY):
    try:
        register_profile(_profile)
    except ValueError as exc:
        if "duplicate profile id" not in str(exc):
            raise

__all__ = ["get_profile", "list_profiles", "register_profile"]
