from pydantic import BaseModel


class ProfileSummary(BaseModel):
    id: str
    name: str
    description: str


class PublicProfileField(BaseModel):
    id: str
    label: str
    level: str
    kind: str
    dtype: str
    description: str | None = None


class ProfileResponse(ProfileSummary):
    fields: list[PublicProfileField]
    primary_date: str
    alternate_dates: list[str]
