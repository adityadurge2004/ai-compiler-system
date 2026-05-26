"""AI Compiler System - FastAPI Application."""

from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from app.config import settings
from app.orchestrator.pipeline import CompilerOrchestrator
from app.schemas.pipeline import (
    GenerateRequest,
    GenerateResponse,
    MetricsResponse,
    PipelineState,
    RepairRequest,
    ValidateRequest,
)
from app.schemas.validation import ValidationReport
from app.services.metrics_service import metrics_service
from app.utils.coerce import normalize_pipeline_state
from app.utils.errors import CompilerException
from app.utils.logging import setup_logging

setup_logging()
orchestrator = CompilerOrchestrator()


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


app = FastAPI(
    title="AI Compiler System",
    description="Natural language to validated executable application configurations",
    version="1.0.0",
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
@app.get("/")
async def root():
    return {
        "message": "AI Compiler System Running Successfully",
        "docs": "http://127.0.0.1:8000/docs",
        "health": "http://127.0.0.1:8000/health"
    }
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health() -> dict[str, Any]:
    return {
        "status": "healthy",
        "service": "ai-compiler",
        "version": "1.0.0",
        "openai_configured": bool(settings.openai_api_key),
    }


@app.post("/api/generate", response_model=GenerateResponse)
async def generate(request: GenerateRequest) -> GenerateResponse:
    try:
        state = normalize_pipeline_state(await orchestrator.generate(request))
        validation = state.validation
        valid = validation.valid if validation else False
        return GenerateResponse(
            success=valid,
            state=state,
            metrics={
                "validation_errors": validation.error_count if validation else 0,
                "repair_actions": len(state.repair_actions),
                "stages_completed": len(state.stages),
                "mode": request.mode,
            },
        )
    except CompilerException as e:
        return GenerateResponse(
            success=False,
            state=PipelineState(prompt=request.prompt),
            error=e.error.model_dump(),
        )
    except Exception as e:
        return GenerateResponse(
            success=False,
            state=PipelineState(prompt=request.prompt),
            error={"code": "INTERNAL_ERROR", "message": str(e)},
        )


@app.post("/api/validate")
async def validate(request: ValidateRequest) -> ValidationReport:
    report = orchestrator.validator.validate(
        intent=request.intent,
        architecture=request.architecture,
        database=request.database,
        api=request.api,
        ui=request.ui,
        auth=request.auth,
    )
    return report


@app.post("/api/repair", response_model=GenerateResponse)
async def repair(request: RepairRequest) -> GenerateResponse:
    try:
        state = PipelineState(
            prompt=request.prompt,
            intent=request.intent,
            architecture=request.architecture,
            database=request.database,
            api=request.api,
            ui=request.ui,
            auth=request.auth,
        )
        normalize_pipeline_state(state)
        report = request.validation_report or await orchestrator.validate_only(state)
        state.validation = report

        if report.valid:
            return GenerateResponse(success=True, state=state, metrics={"message": "No repair needed"})

        state = await orchestrator.repair_only(state, report)
        new_report = await orchestrator.validate_only(state)
        state.validation = new_report

        if new_report.valid and state.database and state.api and state.ui:
            state.runtime = orchestrator.runtime_gen.generate(
                state.database, state.api, state.ui
            )

        return GenerateResponse(
            success=new_report.valid,
            state=state,
            metrics={"repair_actions": len(state.repair_actions)},
        )
    except CompilerException as e:
        return GenerateResponse(
            success=False,
            state=PipelineState(prompt=request.prompt),
            error=e.error.model_dump(),
        )


@app.get("/api/metrics", response_model=MetricsResponse)
async def metrics() -> MetricsResponse:
    return metrics_service.get_metrics()


class EvaluationRunRequest(BaseModel):
    prompts: list[str] = Field(default_factory=list)
    dataset: str = "normal"


@app.post("/api/evaluate")
async def evaluate(request: EvaluationRunRequest) -> dict[str, Any]:
    results = []
    for prompt in request.prompts:
        try:
            state = await orchestrator.generate(GenerateRequest(prompt=prompt, skip_repair=False))
            results.append({
                "prompt": prompt[:80],
                "success": state.validation.valid if state.validation else False,
                "errors": state.validation.error_count if state.validation else -1,
                "repairs": len(state.repair_actions),
            })
        except Exception as e:
            results.append({"prompt": prompt[:80], "success": False, "error": str(e)})
    success = sum(1 for r in results if r.get("success"))
    return {
        "dataset": request.dataset,
        "total": len(results),
        "success": success,
        "success_rate": round(success / len(results) * 100, 2) if results else 0,
        "results": results,
    }
