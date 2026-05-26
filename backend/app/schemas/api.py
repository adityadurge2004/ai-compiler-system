"""API schema definitions."""

from pydantic import BaseModel, Field


class RequestField(BaseModel):
    name: str
    type: str = "string"
    required: bool = True
    description: str = ""


class ResponseField(BaseModel):
    name: str
    type: str = "string"
    description: str = ""


class EndpointDef(BaseModel):
    path: str
    method: str = "GET"
    summary: str = ""
    request_fields: list[RequestField] = Field(default_factory=list)
    response_fields: list[ResponseField] = Field(default_factory=list)
    auth_required: bool = False
    roles: list[str] = Field(default_factory=list)


class ApiSchema(BaseModel):
    base_path: str = "/api/v1"
    endpoints: list[EndpointDef] = Field(default_factory=list)
    version: str = "1.0.0"
