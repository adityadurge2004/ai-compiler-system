"""Stage 2: Architecture Planning."""

import json
from typing import Any

from app.schemas.architecture import ArchitectureSchema
from app.stages.base import BaseStage

ARCH_SYSTEM = """You are an architecture planner for an AI application compiler.
Convert application intent into system architecture. Return ONLY valid JSON:
{
  "entities": ["domain entity names"],
  "services": [{"name": "string", "description": "string", "dependencies": ["other services"]}],
  "pages": [{"name": "string", "route": "/path", "description": "string", "protected": boolean}],
  "flows": [{"name": "string", "steps": ["step descriptions"]}],
  "relationships": [{"from": "EntityA", "to": "EntityB", "type": "one_to_many|many_to_many|one_to_one"}]
}
Rules:
- Align entities with intent features
- Every feature should map to at least one page or service
- Use RESTful route conventions
- Be deterministic"""


class ArchitecturePlanningStage(BaseStage[ArchitectureSchema]):
    name = "architecture_planning"
    output_model = ArchitectureSchema

    @property
    def system_prompt(self) -> str:
        return ARCH_SYSTEM

    def build_user_prompt(self, context: dict[str, Any]) -> str:
        intent = context.get("intent")
        intent_json = intent.model_dump() if hasattr(intent, "model_dump") else intent
        return f"Plan architecture for this intent:\n\n{json.dumps(intent_json, indent=2)}"
