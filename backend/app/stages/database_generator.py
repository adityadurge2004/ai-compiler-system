"""Stage 3: Database Schema Generator."""

import json
from typing import Any

from app.schemas.database import DatabaseSchema
from app.stages.base import BaseStage

DB_SYSTEM = """You are a database schema generator for an AI application compiler.
Generate SQLite-compatible schema. Return ONLY valid JSON:
{
  "tables": [{
    "name": "snake_case_table",
    "fields": [{
      "name": "field_name",
      "type": "INTEGER|TEXT|REAL|BOOLEAN|DATETIME",
      "nullable": boolean,
      "unique": boolean,
      "primary_key": boolean,
      "default": "value or null",
      "references": "table.column or null"
    }],
    "indexes": [{"name": "idx_name", "columns": ["col"], "unique": boolean}]
  }],
  "version": "1.0.0"
}
Rules:
- Include users table if authentication is needed
- Foreign keys via references field
- Primary keys on id fields
- Match architecture entities"""


class DatabaseGeneratorStage(BaseStage[DatabaseSchema]):
    name = "database_generator"
    output_model = DatabaseSchema

    @property
    def system_prompt(self) -> str:
        return DB_SYSTEM

    def build_user_prompt(self, context: dict[str, Any]) -> str:
        return (
            f"Intent:\n{json.dumps(_dump(context.get('intent')), indent=2)}\n\n"
            f"Architecture:\n{json.dumps(_dump(context.get('architecture')), indent=2)}"
        )


def _dump(obj: Any) -> dict:
    if obj is None:
        return {}
    return obj.model_dump() if hasattr(obj, "model_dump") else obj
