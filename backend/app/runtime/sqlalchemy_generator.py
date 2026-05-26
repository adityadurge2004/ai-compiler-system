"""SQLAlchemy models generator."""

from typing import Any

from app.schemas.database import DatabaseSchema
from app.utils.coerce import coerce_database

TYPE_MAP = {
    "INTEGER": "Integer",
    "TEXT": "String",
    "REAL": "Float",
    "BOOLEAN": "Boolean",
    "DATETIME": "DateTime",
}


class SQLAlchemyGenerator:
    def generate(self, schema: DatabaseSchema | dict[str, Any]) -> str:
        db = coerce_database(schema)
        if db is None:
            return '"""No database schema"""'
        lines = [
            '"""Auto-generated SQLAlchemy models."""',
            "from datetime import datetime",
            "from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String, Text",
            "from sqlalchemy.orm import DeclarativeBase, relationship",
            "",
            "",
            "class Base(DeclarativeBase):",
            "    pass",
            "",
        ]
        for table in db.tables:
            class_name = "".join(w.capitalize() for w in table.name.split("_"))
            if class_name.endswith("s") and not class_name.endswith("ss"):
                class_name = class_name[:-1]
            lines.append(f"class {class_name}(Base):")
            lines.append(f'    __tablename__ = "{table.name}"')
            lines.append("")
            for field in table.fields:
                sa_type = TYPE_MAP.get(field.type.upper(), "String")
                args = [sa_type]
                col_args = []
                if field.primary_key:
                    col_args.append("primary_key=True")
                if not field.nullable and not field.primary_key:
                    col_args.append("nullable=False")
                if field.unique:
                    col_args.append("unique=True")
                if field.references:
                    ref = field.references.replace(".", ".")
                    col_args.append(f'ForeignKey("{field.references}")')
                col_str = ", ".join(col_args)
                lines.append(f"    {field.name} = Column({sa_type}{', ' + col_str if col_str else ''})")
            lines.append("")
        return "\n".join(lines)
