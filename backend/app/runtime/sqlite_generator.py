"""SQLite DDL generator."""

from typing import Any

from app.schemas.database import DatabaseSchema, FieldDef, TableDef
from app.utils.coerce import coerce_database


class SQLiteGenerator:
    def generate(self, schema: DatabaseSchema | dict[str, Any]) -> str:
        db = coerce_database(schema)
        if db is None:
            return "-- No database schema"
        lines = ["-- Auto-generated SQLite schema", "PRAGMA foreign_keys = ON;", ""]
        for table in db.tables:
            lines.append(self._table_ddl(table))
            lines.append("")
        return "\n".join(lines)

    def _table_ddl(self, table: TableDef) -> str:
        cols = []
        fks = []
        for field in table.fields:
            col = self._column_def(field)
            cols.append(f"  {col}")
            if field.references:
                ref_table, ref_col = field.references.split(".", 1) if "." in field.references else (field.references, "id")
                fks.append(f"  FOREIGN KEY ({field.name}) REFERENCES {ref_table}({ref_col})")
        for idx in table.indexes:
            unique = "UNIQUE " if idx.unique else ""
            cols_str = ", ".join(idx.columns)
            lines_extra = f"CREATE {unique}INDEX IF NOT EXISTS {idx.name} ON {table.name} ({cols_str});"
        ddl = f"CREATE TABLE IF NOT EXISTS {table.name} (\n" + ",\n".join(cols)
        if fks:
            ddl += ",\n" + ",\n".join(fks)
        ddl += "\n);"
        result = ddl
        for idx in table.indexes:
            unique = "UNIQUE " if idx.unique else ""
            cols_str = ", ".join(idx.columns)
            result += f"\nCREATE {unique}INDEX IF NOT EXISTS {idx.name} ON {table.name} ({cols_str});"
        return result

    def _column_def(self, field: FieldDef) -> str:
        parts = [field.name, field.type]
        if field.primary_key:
            parts.append("PRIMARY KEY")
            if field.type.upper() == "INTEGER":
                parts.append("AUTOINCREMENT")
        if not field.nullable and not field.primary_key:
            parts.append("NOT NULL")
        if field.unique and not field.primary_key:
            parts.append("UNIQUE")
        if field.default is not None:
            default = field.default
            if isinstance(default, str) and default.upper() not in ("NULL", "CURRENT_TIMESTAMP"):
                default = f"'{default}'"
            parts.append(f"DEFAULT {default}")
        return " ".join(parts)
