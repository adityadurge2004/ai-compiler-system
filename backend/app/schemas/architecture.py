"""Architecture planning schema."""

from pydantic import BaseModel, Field


class ServiceDef(BaseModel):
    name: str
    description: str = ""
    dependencies: list[str] = Field(default_factory=list)


class PageDef(BaseModel):
    name: str
    route: str = ""
    description: str = ""
    protected: bool = False


class FlowDef(BaseModel):
    name: str
    steps: list[str] = Field(default_factory=list)


class RelationshipDef(BaseModel):
    from_entity: str = Field(alias="from")
    to_entity: str = Field(alias="to")
    type: str = "one_to_many"

    model_config = {"populate_by_name": True}


class ArchitectureSchema(BaseModel):
    entities: list[str] = Field(default_factory=list)
    services: list[ServiceDef] = Field(default_factory=list)
    pages: list[PageDef] = Field(default_factory=list)
    flows: list[FlowDef] = Field(default_factory=list)
    relationships: list[RelationshipDef] = Field(default_factory=list)
