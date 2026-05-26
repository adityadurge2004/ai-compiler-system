"""Auth rules schema."""

from pydantic import BaseModel, Field


class PermissionDef(BaseModel):
    name: str
    resource: str = ""
    actions: list[str] = Field(default_factory=list)


class RoleDef(BaseModel):
    name: str
    permissions: list[str] = Field(default_factory=list)
    description: str = ""


class RouteProtection(BaseModel):
    route: str
    methods: list[str] = Field(default_factory=list)
    roles: list[str] = Field(default_factory=list)
    public: bool = False


class AuthSchema(BaseModel):
    roles: list[RoleDef] = Field(default_factory=list)
    permissions: list[PermissionDef] = Field(default_factory=list)
    route_protections: list[RouteProtection] = Field(default_factory=list)
    default_role: str = "user"
