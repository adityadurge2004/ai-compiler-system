"""Stage 5: UI Schema Generator."""

import json
from typing import Any

from app.schemas.ui import UiSchema
from app.stages.base import BaseStage

UI_SYSTEM = """You are a UI schema generator for an AI application compiler.
Generate UI specification for a React/Next.js app. Return ONLY valid JSON:
{
  "theme": "dark|light",
  "pages": [{
    "name": "PageName",
    "route": "/path",
    "layout": "default|sidebar|centered",
    "components": [{"name": "ComponentName", "type": "form|table|card|navigation|generic", "props": {}}],
    "forms": [{
      "name": "formName",
      "fields": [{"name": "field", "label": "Label", "type": "text|email|password|select", "required": boolean, "api_binding": "api_field_name"}],
      "submit_endpoint": "/api/v1/..."
    }],
    "api_bindings": ["/api/v1/endpoint paths used"]
  }],
  "global_components": [{"name": "Navbar", "type": "navigation", "props": {}}]
}
Rules:
- One page per architecture page
- Form api_binding must match API request_fields
- api_bindings must reference actual API endpoints"""


class UiGeneratorStage(BaseStage[UiSchema]):
    name = "ui_generator"
    output_model = UiSchema

    @property
    def system_prompt(self) -> str:
        return UI_SYSTEM

    def build_user_prompt(self, context: dict[str, Any]) -> str:
        return (
            f"Intent:\n{json.dumps(_d(context.get('intent')), indent=2)}\n\n"
            f"Architecture:\n{json.dumps(_d(context.get('architecture')), indent=2)}\n\n"
            f"API:\n{json.dumps(_d(context.get('api')), indent=2)}"
        )


def _d(obj: Any) -> dict:
    if obj is None:
        return {}
    return obj.model_dump() if hasattr(obj, "model_dump") else obj
