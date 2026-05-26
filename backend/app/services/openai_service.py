"""OpenAI API service with structured JSON outputs."""

import asyncio
import time
from typing import Any

from openai import AsyncOpenAI, APIError, APITimeoutError, RateLimitError

from app.config import settings
from app.utils.errors import CompilerError, CompilerException, ErrorCode
from app.utils.json_utils import extract_json_from_text
from app.utils.logging import get_logger

logger = get_logger("openai_service")


class OpenAIService:
    """Wraps OpenAI chat completions for pipeline stages."""

    def __init__(self) -> None:
        self._client: AsyncOpenAI | None = None
        self.total_tokens: int = 0
        self.total_requests: int = 0

    @property
    def client(self) -> AsyncOpenAI:
        if not settings.openai_api_key:
            raise CompilerException(
                CompilerError(
                    code=ErrorCode.MISSING_API_KEY,
                    message="OPENAI_API_KEY is not configured",
                    recoverable=False,
                )
            )
        if self._client is None:
            kwargs: dict[str, Any] = {"api_key": settings.openai_api_key}
            if settings.openai_base_url:
                kwargs["base_url"] = settings.openai_base_url
            self._client = AsyncOpenAI(**kwargs)
        return self._client

    async def complete_json(
        self,
        system_prompt: str,
        user_prompt: str,
        stage_name: str = "unknown",
        *,
        temperature: float | None = None,
        max_tokens: int | None = None,
        timeout_seconds: int | None = None,
        retries: int = 1,
        allow_fallback_on_timeout: bool = False,
        allow_fallback_on_invalid_json: bool = False,
    ) -> dict[str, Any]:
        """Request structured JSON from the model."""
        if not settings.openai_api_key:
            return self._fallback_response(stage_name, user_prompt)

        temp = settings.openai_temperature if temperature is None else temperature
        max_toks = settings.openai_max_tokens if max_tokens is None else max_tokens
        timeout = settings.request_timeout_seconds if timeout_seconds is None else timeout_seconds

        last_exc: Exception | None = None
        for attempt in range(max(1, retries) + 1):
            start = time.perf_counter()
            try:
                response = await asyncio.wait_for(
                    self.client.chat.completions.create(
                        model=settings.openai_model,
                        temperature=temp,
                        max_tokens=max_toks,
                        response_format={"type": "json_object"},
                        messages=[
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_prompt},
                        ],
                    ),
                    timeout=timeout,
                )
                last_exc = None
                break
            except (asyncio.TimeoutError, APITimeoutError) as e:
                last_exc = e
                logger.warning(
                    "Stage %s timed out (attempt %s/%s)",
                    stage_name,
                    attempt + 1,
                    max(1, retries) + 1,
                )
                if attempt >= retries:
                    if allow_fallback_on_timeout:
                        logger.warning("Using fallback for %s due to timeout", stage_name)
                        return self._fallback_response(stage_name, user_prompt)
                    raise CompilerException(
                        CompilerError(
                            code=ErrorCode.TIMEOUT,
                            message=f"OpenAI request timed out for stage {stage_name}",
                            details={
                                "stage": stage_name,
                                "attempts": attempt + 1,
                                "timeout_seconds": timeout,
                            },
                        )
                    ) from e
                await asyncio.sleep(min(2.0 * (attempt + 1), 5.0))
            except RateLimitError as e:
                last_exc = e
                raise CompilerException(
                    CompilerError(
                        code=ErrorCode.OPENAI_FAILURE,
                        message="OpenAI rate limit exceeded",
                        details={"stage": stage_name},
                        recoverable=True,
                    )
                ) from e
            except APIError as e:
                last_exc = e
                raise CompilerException(
                    CompilerError(
                        code=ErrorCode.OPENAI_FAILURE,
                        message=f"OpenAI API error: {e.message}",
                        details={"stage": stage_name},
                    )
                ) from e

        if last_exc is not None:
            # Should never happen; defensive
            if allow_fallback_on_timeout:
                return self._fallback_response(stage_name, user_prompt)
            raise CompilerException(
                CompilerError(
                    code=ErrorCode.OPENAI_FAILURE,
                    message=f"OpenAI request failed for stage {stage_name}",
                    details={"stage": stage_name, "error": str(last_exc)},
                )
            ) from last_exc

        elapsed_ms = (time.perf_counter() - start) * 1000
        content = response.choices[0].message.content or "{}"
        usage = response.usage
        if usage:
            self.total_tokens += usage.total_tokens
        self.total_requests += 1

        logger.info(
            "Stage %s completed in %.0fms, tokens=%s",
            stage_name,
            elapsed_ms,
            usage.total_tokens if usage else "?",
        )

        try:
            return extract_json_from_text(content)
        except CompilerException:
            if allow_fallback_on_invalid_json:
                logger.warning("Using fallback for %s due to invalid JSON", stage_name)
                return self._fallback_response(stage_name, user_prompt)
            raise

    def _fallback_response(self, stage_name: str, user_prompt: str) -> dict[str, Any]:
        """Deterministic fallback when no API key (demo/dev mode)."""
        logger.warning("No API key - using deterministic fallback for %s", stage_name)
        prompt_lower = user_prompt.lower()

        if stage_name == "intent_extraction":
            features = []
            for kw in ["login", "auth", "dashboard", "payment", "stripe", "contact", "crm"]:
                if kw in prompt_lower:
                    features.append(kw)
            return {
                "app_type": "CRM" if "crm" in prompt_lower else "WebApp",
                "features": features or ["authentication", "dashboard"],
                "roles": ["admin", "user"],
                "entities": [{"name": "Contact", "description": "CRM contact", "attributes": ["name", "email"]}],
                "integrations": ["stripe"] if "stripe" in prompt_lower or "payment" in prompt_lower else [],
                "constraints": [],
                "normalized_prompt": user_prompt[:500],
            }
        if stage_name == "architecture_planning":
            return {
                "entities": ["User", "Contact", "Payment"],
                "services": [{"name": "AuthService", "description": "Authentication"}, {"name": "ContactService", "description": "Contacts CRUD"}],
                "pages": [{"name": "LoginPage", "route": "/login", "protected": False}, {"name": "DashboardPage", "route": "/dashboard", "protected": True}],
                "flows": [{"name": "LoginFlow", "steps": ["enter_credentials", "validate", "redirect_dashboard"]}],
                "relationships": [{"from": "User", "to": "Contact", "type": "one_to_many"}],
            }
        if stage_name == "database_generator":
            return {
                "tables": [
                    {"name": "users", "fields": [
                        {"name": "id", "type": "INTEGER", "primary_key": True, "nullable": False},
                        {"name": "email", "type": "TEXT", "unique": True, "nullable": False},
                        {"name": "password_hash", "type": "TEXT", "nullable": False},
                        {"name": "role", "type": "TEXT", "default": "user"},
                    ], "indexes": [{"name": "idx_users_email", "columns": ["email"], "unique": True}]},
                    {"name": "contacts", "fields": [
                        {"name": "id", "type": "INTEGER", "primary_key": True, "nullable": False},
                        {"name": "user_id", "type": "INTEGER", "references": "users.id"},
                        {"name": "name", "type": "TEXT", "nullable": False},
                        {"name": "email", "type": "TEXT"},
                    ], "indexes": []},
                ],
                "version": "1.0.0",
            }
        if stage_name == "api_generator":
            return {
                "base_path": "/api/v1",
                "endpoints": [
                    {"path": "/auth/login", "method": "POST", "summary": "Login", "request_fields": [{"name": "email", "type": "string", "required": True}, {"name": "password", "type": "string", "required": True}], "response_fields": [{"name": "token", "type": "string"}], "auth_required": False},
                    {"path": "/contacts", "method": "GET", "summary": "List contacts", "response_fields": [{"name": "contacts", "type": "array"}], "auth_required": True, "roles": ["admin", "user"]},
                    {"path": "/contacts", "method": "POST", "summary": "Create contact", "request_fields": [{"name": "name", "type": "string", "required": True}, {"name": "email", "type": "string"}], "auth_required": True},
                ],
                "version": "1.0.0",
            }
        if stage_name == "ui_generator":
            return {
                "theme": "dark",
                "pages": [
                    {"name": "LoginPage", "route": "/login", "layout": "centered", "components": [{"name": "LoginForm", "type": "form"}], "forms": [{"name": "login", "fields": [{"name": "email", "label": "Email", "type": "email", "api_binding": "email"}, {"name": "password", "label": "Password", "type": "password", "api_binding": "password"}], "submit_endpoint": "/api/v1/auth/login"}], "api_bindings": ["/api/v1/auth/login"]},
                    {"name": "DashboardPage", "route": "/dashboard", "layout": "sidebar", "components": [{"name": "ContactList", "type": "table"}], "forms": [], "api_bindings": ["/api/v1/contacts"]},
                ],
                "global_components": [{"name": "Navbar", "type": "navigation"}],
            }
        if stage_name == "auth_generator":
            return {
                "roles": [{"name": "admin", "permissions": ["contacts:read", "contacts:write", "users:manage"], "description": "Administrator"}, {"name": "user", "permissions": ["contacts:read", "contacts:write"], "description": "Standard user"}],
                "permissions": [{"name": "contacts:read", "resource": "contacts", "actions": ["read"]}, {"name": "contacts:write", "resource": "contacts", "actions": ["create", "update", "delete"]}],
                "route_protections": [{"route": "/dashboard", "methods": ["GET"], "roles": ["admin", "user"], "public": False}, {"route": "/login", "methods": ["GET"], "roles": [], "public": True}],
                "default_role": "user",
            }
        return {}


openai_service = OpenAIService()
