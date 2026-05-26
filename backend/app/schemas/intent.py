"""Intent extraction schema."""

from pydantic import BaseModel, Field


class EntityIntent(BaseModel):
    name: str
    description: str = ""
    attributes: list[str] = Field(default_factory=list)


class IntentSchema(BaseModel):
    app_type: str = Field(..., description="Application type e.g. CRM, E-commerce")
    features: list[str] = Field(default_factory=list)
    roles: list[str] = Field(default_factory=list)
    entities: list[EntityIntent] = Field(default_factory=list)
    integrations: list[str] = Field(default_factory=list)
    constraints: list[str] = Field(default_factory=list)
    normalized_prompt: str = ""
