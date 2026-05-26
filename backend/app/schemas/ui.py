"""UI schema definitions."""

from pydantic import BaseModel, Field


class FormFieldDef(BaseModel):
    name: str
    label: str = ""
    type: str = "text"
    required: bool = True
    api_binding: str = ""


class ComponentDef(BaseModel):
    name: str
    type: str = "generic"
    props: dict[str, str] = Field(default_factory=dict)


class FormDef(BaseModel):
    name: str
    fields: list[FormFieldDef] = Field(default_factory=list)
    submit_endpoint: str = ""


class PageUiDef(BaseModel):
    name: str
    route: str = ""
    layout: str = "default"
    components: list[ComponentDef] = Field(default_factory=list)
    forms: list[FormDef] = Field(default_factory=list)
    api_bindings: list[str] = Field(default_factory=list)


class UiSchema(BaseModel):
    theme: str = "dark"
    pages: list[PageUiDef] = Field(default_factory=list)
    global_components: list[ComponentDef] = Field(default_factory=list)
