"""Structured error types."""

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class ErrorCode(str, Enum):
    VAGUE_PROMPT = "VAGUE_PROMPT"
    CONFLICTING_REQUIREMENTS = "CONFLICTING_REQUIREMENTS"
    INCOMPLETE_REQUEST = "INCOMPLETE_REQUEST"
    INVALID_JSON = "INVALID_JSON"
    OPENAI_FAILURE = "OPENAI_FAILURE"
    TIMEOUT = "TIMEOUT"
    VALIDATION_FAILED = "VALIDATION_FAILED"
    REPAIR_EXHAUSTED = "REPAIR_EXHAUSTED"
    INTERNAL_ERROR = "INTERNAL_ERROR"
    MISSING_API_KEY = "MISSING_API_KEY"


class CompilerError(BaseModel):
    code: ErrorCode
    message: str
    details: dict[str, Any] = Field(default_factory=dict)
    recoverable: bool = False


class CompilerException(Exception):
    def __init__(self, error: CompilerError) -> None:
        self.error = error
        super().__init__(error.message)
