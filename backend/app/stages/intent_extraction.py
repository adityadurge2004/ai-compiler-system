"""Stage 1: Intent Extraction."""

import json
from typing import Any

from app.schemas.intent import IntentSchema
from app.stages.base import BaseStage

INTENT_SYSTEM = """You are an intent extraction engine for an AI application compiler.
Extract structured intent from natural language. Return ONLY valid JSON matching this schema:
{
  "app_type": "string (e.g. CRM, E-commerce, SaaS)",
  "features": ["list of normalized feature names"],
  "roles": ["list of user roles"],
  "entities": [{"name": "string", "description": "string", "attributes": ["field names"]}],
  "integrations": ["third-party services like stripe, sendgrid"],
  "constraints": ["technical or business constraints"],
  "normalized_prompt": "cleaned summary of user intent"
}
Rules:
- Normalize terminology (login/auth -> authentication, RBAC -> role-based access)
- Be deterministic and exhaustive
- Infer reasonable defaults for vague prompts
- Never include markdown or explanation"""


class IntentExtractionStage(BaseStage[IntentSchema]):
    name = "intent_extraction"
    output_model = IntentSchema

    @property
    def system_prompt(self) -> str:
        return INTENT_SYSTEM

    def build_user_prompt(self, context: dict[str, Any]) -> str:
        prompt = context.get("prompt", "")
        if len(prompt.strip()) < 10:
            raise ValueError("Prompt too short for intent extraction")
        return f"Extract intent from this application request:\n\n{prompt}"


def validate_prompt_quality(prompt: str) -> list[str]:
    """Pre-flight checks for vague or conflicting prompts."""
    issues: list[str] = []
    p = prompt.strip().lower()
    if len(p) < 15:
        issues.append("Prompt is too vague - please describe the application type and features")
    vague_only = all(w in p for w in p.split()[:5]) if len(p.split()) < 5 else False
    if vague_only and "app" not in p and "build" not in p:
        issues.append("Prompt lacks specific application requirements")
    if "no auth" in p and ("login" in p or "authentication" in p):
        issues.append("Conflicting requirements: no auth but login requested")
    return issues
