"""Public, data-only industry profile endpoints."""

from fastapi import APIRouter

from bi.api.deps import ProfileServiceDep
from bi.api.schemas.profiles import ProfileResponse, ProfileSummary, PublicProfileField
from bi.profiles.registry import profile_fields

router = APIRouter(prefix="/profiles", tags=["profiles"])


def public_profile(profile) -> ProfileResponse:
    rules = {rule.field_id: rule.level for rule in profile.data.fields}
    terminology = profile.data.terminology.get("es", {})
    return ProfileResponse(
        id=profile.id, name=profile.name, description=profile.description,
        fields=[PublicProfileField(id=field.id, label=terminology.get(field.id, field.id.replace("_", " ").title()), level=rules[field.id], kind=field.kind, dtype=field.dtype, description=field.description_key) for field in profile_fields(profile)],
        primary_date=profile.data.primary_date, alternate_dates=list(profile.data.alternate_dates),
    )


@router.get("", response_model=list[ProfileSummary])
def get_profiles(service: ProfileServiceDep) -> list[ProfileSummary]:
    return [ProfileSummary(id=item.id, name=item.name, description=item.description) for item in service.list()]


@router.get("/{profile_id}", response_model=ProfileResponse)
def get_profile(profile_id: str, service: ProfileServiceDep) -> ProfileResponse:
    return public_profile(service.get(profile_id))
