"""Pipeline metrics tracking."""

import time
from typing import Any

from app.schemas.pipeline import MetricsResponse


class MetricsService:
    def __init__(self) -> None:
        self.runs: list[dict[str, Any]] = []

    def record_run(
        self,
        success: bool,
        latency_ms: float,
        validation_failures: int = 0,
        repair_count: int = 0,
        retries: int = 0,
        tokens: int = 0,
        prompt_preview: str = "",
    ) -> None:
        cost = tokens * 0.000002  # rough estimate per token
        self.runs.append({
            "timestamp": time.time(),
            "success": success,
            "latency_ms": latency_ms,
            "validation_failures": validation_failures,
            "repair_count": repair_count,
            "retries": retries,
            "tokens": tokens,
            "estimated_cost": cost,
            "prompt_preview": prompt_preview[:100],
        })
        if len(self.runs) > 500:
            self.runs = self.runs[-500:]

    def get_metrics(self) -> MetricsResponse:
        if not self.runs:
            return MetricsResponse()
        total = len(self.runs)
        successful = sum(1 for r in self.runs if r["success"])
        return MetricsResponse(
            total_runs=total,
            successful_runs=successful,
            success_rate=round(successful / total * 100, 2),
            total_retries=sum(r.get("retries", 0) for r in self.runs),
            total_validation_failures=sum(r.get("validation_failures", 0) for r in self.runs),
            total_repairs=sum(r.get("repair_count", 0) for r in self.runs),
            average_latency_ms=round(sum(r["latency_ms"] for r in self.runs) / total, 2),
            estimated_token_cost=round(sum(r.get("estimated_cost", 0) for r in self.runs), 4),
            recent_runs=self.runs[-20:][::-1],
        )


metrics_service = MetricsService()
