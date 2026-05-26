"""Coerce dict/JSON values into typed Pydantic layer models."""

from typing import Any, TypeVar

from pydantic import BaseModel

from app.schemas.api import ApiSchema
from app.schemas.architecture import ArchitectureSchema
from app.schemas.auth import AuthSchema
from app.schemas.database import DatabaseSchema
from app.schemas.intent import IntentSchema
from app.schemas.pipeline import PipelineState
from app.schemas.ui import UiSchema

T = TypeVar("T", bound=BaseModel)


def _coerce(model: type[T], value: Any) -> T | None:
    if value is None:
        return None
    if isinstance(value, model):
        return value
    if isinstance(value, dict):
        return model.model_validate(value)
    raise TypeError(f"Cannot coerce {type(value).__name__} to {model.__name__}")


def normalize_database_dict(data: dict[str, Any]) -> dict[str, Any]:
    """Fix common LLM shapes (table_name, string fields, tables as object)."""
    if "tables" not in data:
        if isinstance(data.get("database"), dict):
            data = data["database"]
        elif isinstance(data.get("database_schema"), dict):
            data = data["database_schema"]
        elif isinstance(data.get("schema"), dict):
            data = data["schema"]

    tables_raw = data.get("tables", [])
    if isinstance(tables_raw, dict):
        tables_raw = [
            {"name": k, "fields": v if isinstance(v, list) else []}
            for k, v in tables_raw.items()
        ]
    if not isinstance(tables_raw, list):
        tables_raw = []

    tables: list[dict[str, Any]] = []
    for table in tables_raw:
        if not isinstance(table, dict):
            continue
        name = table.get("name") or table.get("table_name") or "unnamed_table"
        fields_raw = table.get("fields", [])
        fields: list[dict[str, Any]] = []
        if isinstance(fields_raw, list):
            for f in fields_raw:
                if isinstance(f, str):
                    fields.append({"name": f, "type": "TEXT", "nullable": True})
                elif isinstance(f, dict) and f.get("name"):
                    fields.append(f)
        tables.append({
            "name": name,
            "fields": fields,
            "indexes": table.get("indexes", []) if isinstance(table.get("indexes"), list) else [],
        })

    return {
        "tables": tables,
        "version": data.get("version", "1.0.0"),
    }


def coerce_database(value: Any) -> DatabaseSchema | None:
    if value is None:
        return None
    if isinstance(value, DatabaseSchema):
        return value
    if isinstance(value, dict):
        return DatabaseSchema.model_validate(normalize_database_dict(value))
    raise TypeError(f"Cannot coerce database from {type(value).__name__}")


def coerce_intent(value: Any) -> IntentSchema | None:
    return _coerce(IntentSchema, value)


def coerce_architecture(value: Any) -> ArchitectureSchema | None:
    return _coerce(ArchitectureSchema, value)


def coerce_api(value: Any) -> ApiSchema | None:
    return _coerce(ApiSchema, value)


def coerce_ui(value: Any) -> UiSchema | None:
    return _coerce(UiSchema, value)


def coerce_auth(value: Any) -> AuthSchema | None:
    return _coerce(AuthSchema, value)


def normalize_pipeline_state(state: PipelineState) -> PipelineState:
    """Ensure all layer fields are Pydantic models, not raw dicts."""
    return PipelineState(
        prompt=state.prompt,
        intent=coerce_intent(state.intent),
        architecture=coerce_architecture(state.architecture),
        database=coerce_database(state.database),
        api=coerce_api(state.api),
        ui=coerce_ui(state.ui),
        auth=coerce_auth(state.auth),
        validation=state.validation,
        runtime=state.runtime,
        stages=state.stages,
        repair_actions=state.repair_actions,
        logs=state.logs,
    )
