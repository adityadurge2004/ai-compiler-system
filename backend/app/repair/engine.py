"""Repair Engine - targeted regeneration of failing sections."""

import json
from typing import Any

from app.repair.classifier import ErrorClassifier
from app.schemas.pipeline import PipelineState
from app.schemas.validation import ValidationReport
from app.stages.architecture_planning import ArchitecturePlanningStage
from app.stages.api_generator import ApiGeneratorStage
from app.stages.auth_generator import AuthGeneratorStage
from app.stages.database_generator import DatabaseGeneratorStage
from app.stages.intent_extraction import IntentExtractionStage
from app.stages.ui_generator import UiGeneratorStage
from app.services.openai_service import OpenAIService
from app.utils.coerce import normalize_pipeline_state
from app.utils.logging import PipelineLogger
from app.validators.engine import ValidationEngine

REPAIR_CONTEXT_TEMPLATE = """The following validation errors were found in the {layer} layer.
Regenerate ONLY this layer to fix these issues. Do not change unrelated parts.

Validation errors:
{errors}

Current {layer} schema:
{current}

Upstream context for reference:
{context}

Return the complete corrected {layer} JSON schema."""


class RepairEngine:
    def __init__(
        self,
        openai: OpenAIService,
        validator: ValidationEngine,
        logger: PipelineLogger,
    ) -> None:
        self.openai = openai
        self.validator = validator
        self.logger = logger
        self.classifier = ErrorClassifier()
        self._stages = {
            "intent": IntentExtractionStage,
            "architecture": ArchitecturePlanningStage,
            "database": DatabaseGeneratorStage,
            "api": ApiGeneratorStage,
            "ui": UiGeneratorStage,
            "auth": AuthGeneratorStage,
        }

    async def repair(
        self,
        state: PipelineState,
        report: ValidationReport,
        prompt: str = "",
    ) -> tuple[PipelineState, list[dict[str, Any]]]:
        actions: list[dict[str, Any]] = []
        grouped = self.classifier.classify(report)
        repair_order = self.classifier.get_repair_order(grouped)

        if not repair_order:
            self.logger.log("repair", "info", "No repairable errors found")
            return state, actions

        for layer in repair_order:
            issues = grouped[layer]
            self.logger.log(
                "repair",
                "info",
                f"Targeted repair for layer '{layer}' ({len(issues)} issues)",
            )

            action = await self._repair_layer(state, layer, issues, prompt)
            actions.append(action)

            state = normalize_pipeline_state(state)
            context = self._build_context(state, prompt)
            new_report = self.validator.validate(
                intent=state.intent,
                architecture=state.architecture,
                database=state.database,
                api=state.api,
                ui=state.ui,
                auth=state.auth,
            )
            state.validation = new_report

            if new_report.valid:
                self.logger.log("repair", "info", "Validation passed after repair")
                break

        return state, actions

    async def _repair_layer(
        self,
        state: PipelineState,
        layer: str,
        issues: list,
        prompt: str,
    ) -> dict[str, Any]:
        stage_cls = self._stages.get(layer)
        if not stage_cls:
            return {"layer": layer, "status": "skipped", "reason": "unknown layer"}

        current = getattr(state, layer, None)
        current_json = current.model_dump() if current else {}

        error_text = "\n".join(f"- [{i.category}] {i.message}" for i in issues)
        context = self._build_context(state, prompt)

        repair_prompt = REPAIR_CONTEXT_TEMPLATE.format(
            layer=layer,
            errors=error_text,
            current=json.dumps(current_json, indent=2),
            context=json.dumps({k: v for k, v in context.items() if k != layer}, indent=2)[:3000],
        )

        stage = stage_cls(self.openai, self.logger)
        raw = await self.openai.complete_json(
            stage.system_prompt + "\n\nYou are REPAIRING a failed schema. Fix only the reported issues.",
            repair_prompt if layer != "intent" else (prompt or state.prompt),
            stage_name=f"repair_{layer}",
        )

        if layer == "database" and isinstance(raw, dict):
            from app.utils.coerce import normalize_database_dict
            raw = normalize_database_dict(raw)

        output_model = stage.output_model
        repaired = output_model.model_validate(raw)
        setattr(state, layer, repaired)
        normalize_pipeline_state(state)

        return {
            "layer": layer,
            "status": "repaired",
            "issues_fixed": len(issues),
            "issue_messages": [i.message for i in issues],
        }

    def _build_context(self, state: PipelineState, prompt: str) -> dict[str, Any]:
        state = normalize_pipeline_state(state)
        ctx: dict[str, Any] = {"prompt": prompt or state.prompt}
        for key in ("intent", "architecture", "database", "api", "ui", "auth"):
            val = getattr(state, key, None)
            if val is not None and hasattr(val, "model_dump"):
                ctx[key] = val.model_dump()
        return ctx
