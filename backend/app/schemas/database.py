"""Database schema definitions."""

from pydantic import BaseModel, Field


class FieldDef(BaseModel):
    name: str
    type: str = "TEXT"
    nullable: bool = True
    unique: bool = False
    primary_key: bool = False
    default: str | None = None
    references: str | None = None


class IndexDef(BaseModel):
    name: str
    columns: list[str] = Field(default_factory=list)
    unique: bool = False


class TableDef(BaseModel):
    name: str
    fields: list[FieldDef] = Field(default_factory=list)
    indexes: list[IndexDef] = Field(default_factory=list)


class DatabaseSchema(BaseModel):
    tables: list[TableDef] = Field(default_factory=list)
    version: str = "1.0.0"
