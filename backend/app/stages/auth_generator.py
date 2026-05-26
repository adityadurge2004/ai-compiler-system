"""Stage 6: Auth Rules Generator."""

import json
from typing import Any

from app.schemas.auth import AuthSchema
from app.stages.base import BaseStage

AUTH_SYSTEM = """You are an auth rules generator for an AI application compiler.
Generate RBAC authorization rules. Return ONLY valid JSON:
{
  "roles": [{"name": "role", "permissions": ["perm:name"], "description": ""}],
  "permissions": [{"name": "resource:action", "resource": "resource", "actions": ["read","write"]}],
  "route_protections": [{"route": "/path", "methods": ["GET"], "roles": ["role"], "public": boolean}],
  "default_role": "user"
}
Rules:
- Align roles with intent.roles
- Protect all non-public pages and API endpoints
- Admin role gets elevated permissions
- Map permissions to API resources"""


class AuthGeneratorStage(BaseStage[AuthSchema]):
    name = "auth_generator"
    output_model = AuthSchema

    @property
    def system_prompt(self) -> str:
        return AUTH_SYSTEM

    def build_user_prompt(self, context: dict[str, Any]) -> str:
        return (
            f"Intent:\n{json.dumps(_d(context.get('intent')), indent=2)}\n\n"
            f"Architecture:\n{json.dumps(_d(context.get('architecture')), indent=2)}\n\n"
            f"API:\n{json.dumps(_d(context.get('api')), indent=2)}\n\n"
            f"UI:\n{json.dumps(_d(context.get('ui')), indent=2)}"
        )


def _d(obj: Any) -> dict:
    if obj is None:
        return {}
    return obj.model_dump() if hasattr(obj, "model_dump") else obj
