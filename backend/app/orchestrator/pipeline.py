"""Compiler Orchestrator - multi-stage pipeline execution."""

import time
import json
import hashlib
from typing import Any

from app.config import settings
from app.repair.engine import RepairEngine
from app.runtime.generator import RuntimeGenerator
from app.schemas.pipeline import GenerateRequest, PipelineState, StageResult
from app.schemas.validation import ValidationReport
from app.services.metrics_service import metrics_service
from app.services.openai_service import openai_service
from app.stages.architecture_planning import ArchitecturePlanningStage
from app.stages.api_generator import ApiGeneratorStage
from app.stages.auth_generator import AuthGeneratorStage
from app.stages.database_generator import DatabaseGeneratorStage
from app.stages.intent_extraction import IntentExtractionStage, validate_prompt_quality
from app.stages.ui_generator import UiGeneratorStage
from app.utils.coerce import (
    coerce_api,
    coerce_architecture,
    coerce_auth,
    coerce_database,
    coerce_intent,
    coerce_ui,
    normalize_pipeline_state,
)

_LAYER_COERCERS = {
    "intent": coerce_intent,
    "architecture": coerce_architecture,
    "database": coerce_database,
    "api": coerce_api,
    "ui": coerce_ui,
    "auth": coerce_auth,
}
from app.utils.errors import CompilerError, CompilerException, ErrorCode
from app.utils.logging import PipelineLogger
from app.validators.engine import ValidationEngine


class CompilerOrchestrator:
    """
    AI Compiler pipeline:
    Intent → Architecture → DB → API → UI → Auth → Validate → Repair → Runtime
    """

    STAGES = [
        ("intent_extraction", IntentExtractionStage, "intent"),
        ("architecture_planning", ArchitecturePlanningStage, "architecture"),
        ("database_generator", DatabaseGeneratorStage, "database"),
        ("api_generator", ApiGeneratorStage, "api"),
        ("ui_generator", UiGeneratorStage, "ui"),
        ("auth_generator", AuthGeneratorStage, "auth"),
    ]

    def __init__(self) -> None:
        self.validator = ValidationEngine()
        self.runtime_gen = RuntimeGenerator()
        self._cache: dict[str, dict[str, Any]] = {}

    def _cache_key(self, stage_name: str, context: dict[str, Any], mode: str) -> str:
        def dump(v: Any) -> Any:
            if hasattr(v, "model_dump"):
                return v.model_dump()
            return v

        payload = {
            "stage": stage_name,
            "mode": mode,
            "prompt": context.get("prompt", ""),
            "intent": dump(context.get("intent")),
            "architecture": dump(context.get("architecture")),
            "database": dump(context.get("database")),
            "api": dump(context.get("api")),
            "ui": dump(context.get("ui")),
            "auth": dump(context.get("auth")),
        }
        raw = json.dumps(payload, sort_keys=True, default=str).encode("utf-8")
        return hashlib.sha256(raw).hexdigest()

    async def generate(self, request: GenerateRequest) -> PipelineState:
        start = time.perf_counter()
        plog = PipelineLogger()
        state = PipelineState(prompt=request.prompt, logs=[])

        quality_issues = validate_prompt_quality(request.prompt)
        if quality_issues:
            plog.log("preflight", "warning", quality_issues[0])

        mode = (request.mode or "full").lower().strip()
        if mode not in ("full", "fast"):
            mode = "full"

        # Fast mode: smaller generations + less repair
        llm_overrides = {}
        if mode == "fast":
            llm_overrides = {
                "temperature": 0.0,
                "max_tokens": 1024,
                "timeout_seconds": 60,
                "retries": 1,
                "allow_fallback_on_timeout": True,
                "allow_fallback_on_invalid_json": True,
            }

        context: dict[str, Any] = {"prompt": request.prompt, "llm": llm_overrides}
        repair_count = 0

        try:
            for stage_name, stage_cls, attr in self.STAGES:
                cache_key = self._cache_key(stage_name, context, mode)
                cached = self._cache.get(cache_key)
                if cached is not None:
                    stage = stage_cls(openai_service, plog)
                    result = stage.output_model.model_validate(cached["output"])
                    duration_ms = 0.0
                    plog.log(stage_name, "info", "Cache hit")
                else:
                    stage = stage_cls(openai_service, plog)
                    result, duration_ms = await stage.run(context)
                    self._cache[cache_key] = {"output": result.model_dump(), "ts": time.time()}

                coercer = _LAYER_COERCERS.get(attr)
                if coercer is not None and result is not None:
                    result = coercer(result)
                state = normalize_pipeline_state(
                    state.model_copy(update={attr: result})
                )
                context[attr] = getattr(state, attr)
                state.stages.append(
                    StageResult(
                        stage=stage_name,
                        status="completed",
                        duration_ms=duration_ms,
                        output=result.model_dump(),
                    )
                )

            state = normalize_pipeline_state(state)
            report = self.validator.validate(
                intent=state.intent,
                architecture=state.architecture,
                database=state.database,
                api=state.api,
                ui=state.ui,
                auth=state.auth,
            )
            state.validation = report
            state.stages.append(
                StageResult(
                    stage="validation",
                    status="passed" if report.valid else "failed",
                    output=report.model_dump(),
                )
            )

            max_repairs = request.max_repair_iterations or settings.max_repair_iterations
            if mode == "fast":
                max_repairs = min(max_repairs, 1)

            if not report.valid and not request.skip_repair and mode != "fast":
                repair_engine = RepairEngine(openai_service, self.validator, plog)
                for iteration in range(max_repairs):
                    plog.log("repair", "info", f"Repair iteration {iteration + 1}/{max_repairs}")
                    state, actions = await repair_engine.repair(state, report, request.prompt)
                    state.repair_actions.extend(actions)
                    repair_count += len(actions)
                    report = state.validation or report
                    if report.valid:
                        break

                state.stages.append(
                    StageResult(
                        stage="repair",
                        status="completed" if report.valid else "partial",
                        output={"iterations": repair_count, "actions": state.repair_actions},
                    )
                )

            state = normalize_pipeline_state(state)
            if state.database and state.api and state.ui:
                runtime_start = time.perf_counter()
                state.runtime = self.runtime_gen.generate(
                    state.database,
                    state.api,
                    state.ui,
                )
                rt_ms = (time.perf_counter() - runtime_start) * 1000
                state.stages.append(
                    StageResult(
                        stage="runtime_generator",
                        status="completed",
                        duration_ms=rt_ms,
                        output={
                            "artifacts": [
                                "sqlite_schema",
                                "sqlalchemy_models",
                                "fastapi_routes",
                                "react_form_configs",
                            ]
                        },
                    )
                )

            state.logs = plog.entries
            elapsed = (time.perf_counter() - start) * 1000

            metrics_service.record_run(
                success=report.valid,
                latency_ms=elapsed,
                validation_failures=report.error_count,
                repair_count=repair_count,
                tokens=openai_service.total_tokens,
                prompt_preview=request.prompt,
            )

            return normalize_pipeline_state(state)

        except CompilerException:
            raise
        except Exception as e:
            raise CompilerException(
                CompilerError(
                    code=ErrorCode.INTERNAL_ERROR,
                    message=str(e),
                    details={"type": type(e).__name__},
                )
            ) from e

    async def validate_only(self, state: PipelineState) -> ValidationReport:
        normalize_pipeline_state(state)
        return self.validator.validate(
            intent=state.intent,
            architecture=state.architecture,
            database=state.database,
            api=state.api,
            ui=state.ui,
            auth=state.auth,
        )

    async def repair_only(self, state: PipelineState, report: ValidationReport) -> PipelineState:
        state = normalize_pipeline_state(state)
        plog = PipelineLogger()
        repair_engine = RepairEngine(openai_service, self.validator, plog)
        state, actions = await repair_engine.repair(state, report, state.prompt)
        state.repair_actions.extend(actions)
        state.logs.extend(plog.entries)
        return normalize_pipeline_state(state)
