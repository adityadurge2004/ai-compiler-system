"""Base class for pipeline stages."""

import time
from abc import ABC, abstractmethod
from typing import Any, Generic, TypeVar

from pydantic import BaseModel

from app.services.openai_service import OpenAIService
from app.utils.logging import PipelineLogger

T = TypeVar("T", bound=BaseModel)


class BaseStage(ABC, Generic[T]):
    name: str = "base"
    output_model: type[T]

    def __init__(self, openai: OpenAIService, logger: PipelineLogger) -> None:
        self.openai = openai
        self.logger = logger

    @property
    @abstractmethod
    def system_prompt(self) -> str:
        pass

    @abstractmethod
    def build_user_prompt(self, context: dict[str, Any]) -> str:
        pass

    async def run(self, context: dict[str, Any]) -> tuple[T, float]:
        start = time.perf_counter()
        self.logger.log(self.name, "info", f"Starting stage: {self.name}")
        user_prompt = self.build_user_prompt(context)
        llm = context.get("llm", {}) if isinstance(context.get("llm"), dict) else {}
        raw = await self.openai.complete_json(
            self.system_prompt,
            user_prompt,
            stage_name=self.name,
            temperature=llm.get("temperature"),
            max_tokens=llm.get("max_tokens"),
            timeout_seconds=llm.get("timeout_seconds"),
            retries=llm.get("retries", 1),
            allow_fallback_on_timeout=llm.get("allow_fallback_on_timeout", False),
            allow_fallback_on_invalid_json=llm.get("allow_fallback_on_invalid_json", False),
        )
        if self.name == "database_generator" and isinstance(raw, dict):
            from app.utils.coerce import normalize_database_dict
            raw = normalize_database_dict(raw)
        result = self.output_model.model_validate(raw)
        duration_ms = (time.perf_counter() - start) * 1000
        self.logger.log(self.name, "info", f"Completed in {duration_ms:.0f}ms")
        return result, duration_ms
