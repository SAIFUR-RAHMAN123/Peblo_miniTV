from pydantic import BaseModel, Field, field_validator

from app.core.reference_data import allowed_languages

ALLOWED_STATUSES = {"draft", "published"}


class EpisodeBase(BaseModel):
    episode_id: str = Field(min_length=1, max_length=50)
    show_id: int
    season_number: int = Field(ge=0)
    episode_number: int = Field(ge=1)
    episode_title: str = Field(min_length=1, max_length=300)
    duration_seconds: int | None = Field(default=None, ge=1)
    language: str
    content_group: str = Field(min_length=1, max_length=120)
    status: str = "draft"

    @field_validator("language")
    @classmethod
    def validate_language(cls, v: str) -> str:
        if v not in allowed_languages():
            raise ValueError(f"'{v}' is not an allowed language. Allowed: {', '.join(allowed_languages())}")
        return v

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        if v not in ALLOWED_STATUSES:
            raise ValueError(f"'{v}' is not a valid status. Allowed: {', '.join(ALLOWED_STATUSES)}")
        return v


class EpisodeCreate(EpisodeBase):
    pass


class EpisodeUpdate(BaseModel):
    episode_title: str | None = None
    duration_seconds: int | None = Field(default=None, ge=1)
    language: str | None = None
    content_group: str | None = None
    status: str | None = None
    season_number: int | None = Field(default=None, ge=0)
    episode_number: int | None = Field(default=None, ge=1)

    @field_validator("language")
    @classmethod
    def validate_language(cls, v: str | None) -> str | None:
        if v is not None and v not in allowed_languages():
            raise ValueError(f"'{v}' is not an allowed language. Allowed: {', '.join(allowed_languages())}")
        return v

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str | None) -> str | None:
        if v is not None and v not in ALLOWED_STATUSES:
            raise ValueError(f"'{v}' is not a valid status. Allowed: {', '.join(ALLOWED_STATUSES)}")
        return v


class EpisodeOut(EpisodeBase):
    id: int

    model_config = {"from_attributes": True}