from pydantic import BaseModel, Field, field_validator

from app.core.reference_data import allowed_categories, allowed_sections


class ShowBase(BaseModel):
    slug: str = Field(min_length=1, max_length=200)
    title: str = Field(min_length=1, max_length=300)
    section: str | None = None
    synopsis: str = ""
    categories: list[str] = Field(default_factory=list)

    @field_validator("section")
    @classmethod
    def validate_section(cls, v: str | None) -> str | None:
        if v is not None and v not in allowed_sections():
            raise ValueError(f"'{v}' is not an allowed section. Allowed: {', '.join(allowed_sections())}")
        return v

    @field_validator("categories")
    @classmethod
    def validate_categories(cls, v: list[str]) -> list[str]:
        bad = [c for c in v if c not in allowed_categories()]
        if bad:
            raise ValueError(f"Unknown categories: {', '.join(bad)}. Allowed: {', '.join(allowed_categories())}")
        return v


class ShowCreate(ShowBase):
    pass


class ShowUpdate(BaseModel):
    title: str | None = None
    section: str | None = None
    synopsis: str | None = None
    categories: list[str] | None = None

    @field_validator("section")
    @classmethod
    def validate_section(cls, v: str | None) -> str | None:
        if v is not None and v not in allowed_sections():
            raise ValueError(f"'{v}' is not an allowed section. Allowed: {', '.join(allowed_sections())}")
        return v

    @field_validator("categories")
    @classmethod
    def validate_categories(cls, v: list[str] | None) -> list[str] | None:
        if v is None:
            return v
        bad = [c for c in v if c not in allowed_categories()]
        if bad:
            raise ValueError(f"Unknown categories: {', '.join(bad)}. Allowed: {', '.join(allowed_categories())}")
        return v


class ShowOut(ShowBase):
    id: int

    model_config = {"from_attributes": True}