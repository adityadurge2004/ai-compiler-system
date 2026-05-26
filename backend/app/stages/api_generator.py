"""Stage 4: API Schema Generator."""

import json
from typing import Any

from app.schemas.api import ApiSchema
from app.stages.base import BaseStage

API_SYSTEM = """You are an API schema generator for an AI application compiler.
Generate REST API specification. Return ONLY valid JSON:
{
  "base_path": "/api/v1",
  "endpoints": [{
    "path": "/resource",
    "method": "GET|POST|PUT|PATCH|DELETE",
    "summary": "description",
    "request_fields": [{"name": "field", "type": "string|integer|boolean|array|object", "required": boolean, "description": ""}],
    "response_fields": [{"name": "field", "type": "string", "description": ""}],
    "auth_required": boolean,
    "roles": ["allowed roles"]
  }],
  "version": "1.0.0"
}
Rules:
- CRUD endpoints for each entity
- Auth endpoints if authentication feature present
- Field names must align with database tables
- Use plural resource names"""


class ApiGeneratorStage(BaseStage[ApiSchema]):
    name = "api_generator"
    output_model = ApiSchema

    @property
    def system_prompt(self) -> str:
        return API_SYSTEM

    def build_user_prompt(self, context: dict[str, Any]) -> str:
        return (
            f"Intent:\n{json.dumps(_d(context.get('intent')), indent=2)}\n\n"
            f"Architecture:\n{json.dumps(_d(context.get('architecture')), indent=2)}\n\n"
            f"Database:\n{json.dumps(_d(context.get('database')), indent=2)}"
        )


def _d(obj: Any) -> dict:
    if obj is None:
        return {}
    return obj.model_dump() if hasattr(obj, "model_dump") else obj
