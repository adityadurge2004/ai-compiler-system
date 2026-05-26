"""JSON parsing and normalization utilities."""

import json
import re
from typing import Any

from app.utils.errors import CompilerError, CompilerException, ErrorCode


def extract_json_from_text(text: str) -> dict[str, Any]:
    """Extract JSON object from LLM response, handling markdown fences."""
    text = text.strip()
    fence_match = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
    if fence_match:
        text = fence_match.group(1).strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        try:
            return json.loads(text[start : end + 1])
        except json.JSONDecodeError as e:
            raise CompilerException(
                CompilerError(
                    code=ErrorCode.INVALID_JSON,
                    message="Failed to parse JSON from model response",
                    details={"parse_error": str(e), "snippet": text[:500]},
                )
            ) from e
    raise CompilerException(
        CompilerError(
            code=ErrorCode.INVALID_JSON,
            message="No valid JSON object found in response",
            details={"snippet": text[:500]},
        )
    )


def normalize_key(key: str) -> str:
    return re.sub(r"[^a-zA-Z0-9_]", "_", key.strip().lower())


def snake_to_camel(name: str) -> str:
    parts = name.split("_")
    return parts[0] + "".join(p.capitalize() for p in parts[1:])
