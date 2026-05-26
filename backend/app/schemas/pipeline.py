"""Pipeline request/response schemas."""

from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.schemas.intent import IntentSchema
from app.schemas.architecture import ArchitectureSchema
from app.schemas.database import DatabaseSchema
from app.schemas.api import ApiSchema
from app.schemas.ui import UiSchema
from app.schemas.auth import AuthSchema
from app.schemas.validation import ValidationReport


class GenerateRequest(BaseModel):
    prompt: str = Field(..., min_length=10, max_length=10000)
    mode: str = Field(default="full", description="full|fast")
    skip_repair: bool = False
    max_repair_iterations: int | None = None


class ValidateRequest(BaseModel):
    intent: IntentSchema | None = None
    architecture: ArchitectureSchema | None = None
    database: DatabaseSchema | None = None
    api: ApiSchema | None = None
    ui: UiSchema | None = None
    auth: AuthSchema | None = None


class RepairRequest(BaseModel):
    prompt: str = ""
    intent: IntentSchema | None = None
    architecture: ArchitectureSchema | None = None
    database: DatabaseSchema | None = None
    api: ApiSchema | None = None
    ui: UiSchema | None = None
    auth: AuthSchema | None = None
    validation_report: ValidationReport | None = None


class RuntimeArtifacts(BaseModel):
    sqlite_schema: str = ""
    sqlalchemy_models: str = ""
    fastapi_routes: str = ""
    react_form_configs: str = ""


class StageResult(BaseModel):
    stage: str
    status: str
    duration_ms: float = 0
    output: dict[str, Any] = Field(default_factory=dict)
    logs: list[dict[str, Any]] = Field(default_factory=list)


class PipelineState(BaseModel):
    model_config = ConfigDict(validate_assignment=True)

    prompt: str = ""
    intent: IntentSchema | None = None
    architecture: ArchitectureSchema | None = None
    database: DatabaseSchema | None = None
    api: ApiSchema | None = None
    ui: UiSchema | None = None
    auth: AuthSchema | None = None
    validation: ValidationReport | None = None
    runtime: RuntimeArtifacts | None = None
    stages: list[StageResult] = Field(default_factory=list)
    repair_actions: list[dict[str, Any]] = Field(default_factory=list)
    logs: list[dict[str, Any]] = Field(default_factory=list)

    @model_validator(mode="after")
    def _ensure_typed_layers(self) -> "PipelineState":
        """Fix model_copy() leaving layer fields as plain dicts."""
        from app.utils.coerce import (
            coerce_api,
            coerce_architecture,
            coerce_auth,
            coerce_database,
            coerce_intent,
            coerce_ui,
        )

        updates: dict[str, Any] = {}
        if isinstance(self.intent, dict):
            updates["intent"] = coerce_intent(self.intent)
        if isinstance(self.architecture, dict):
            updates["architecture"] = coerce_architecture(self.architecture)
        if isinstance(self.database, dict):
            updates["database"] = coerce_database(self.database)
        if isinstance(self.api, dict):
            updates["api"] = coerce_api(self.api)
        if isinstance(self.ui, dict):
            updates["ui"] = coerce_ui(self.ui)
        if isinstance(self.auth, dict):
            updates["auth"] = coerce_auth(self.auth)

        if updates:
            return self.model_copy(update=updates)
        return self


class GenerateResponse(BaseModel):
    success: bool
    state: PipelineState
    error: dict[str, Any] | None = None
    metrics: dict[str, Any] = Field(default_factory=dict)


class MetricsResponse(BaseModel):
    total_runs: int = 0
    successful_runs: int = 0
    success_rate: float = 0.0
    total_retries: int = 0
    total_validation_failures: int = 0
    total_repairs: int = 0
    average_latency_ms: float = 0.0
    estimated_token_cost: float = 0.0
    recent_runs: list[dict[str, Any]] = Field(default_factory=list)
