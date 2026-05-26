"""Missing field and schema mismatch validators."""

from typing import Any

from app.schemas.validation import IssueCategory, IssueSeverity, ValidationIssue
from app.utils.coerce import (
    coerce_api,
    coerce_architecture,
    coerce_auth,
    coerce_database,
    coerce_intent,
    coerce_ui,
)


class FieldValidator:
    def validate_layer(self, layer_name: str, data: Any) -> list[ValidationIssue]:
        issues: list[ValidationIssue] = []
        data = self._ensure_model(layer_name, data)
        if data is None:
            return issues
        dumped = data.model_dump() if hasattr(data, "model_dump") else data

        if layer_name == "intent":
            if not dumped.get("app_type"):
                issues.append(self._missing("intent", "app_type"))
            if not dumped.get("features"):
                issues.append(ValidationIssue(
                    category=IssueCategory.MISSING_FIELD,
                    severity=IssueSeverity.WARNING,
                    message="No features extracted from intent",
                    layer="intent",
                    field="features",
                    repairable=True,
                    repair_target="intent",
                ))

        if layer_name == "architecture":
            if not dumped.get("entities"):
                issues.append(self._missing("architecture", "entities"))
            if not dumped.get("pages"):
                issues.append(self._missing("architecture", "pages"))

        if layer_name == "database":
            for table in dumped.get("tables", []):
                if not table.get("fields"):
                    issues.append(ValidationIssue(
                        category=IssueCategory.SCHEMA_MISMATCH,
                        severity=IssueSeverity.ERROR,
                        message=f"Table '{table.get('name')}' has no fields",
                        layer="database",
                        field=table.get("name", ""),
                        repairable=True,
                        repair_target="database",
                    ))

        if layer_name == "api":
            for ep in dumped.get("endpoints", []):
                if not ep.get("path"):
                    issues.append(self._missing("api", "path", "endpoint missing path"))
                method = ep.get("method", "").upper()
                if method not in ("GET", "POST", "PUT", "PATCH", "DELETE"):
                    issues.append(ValidationIssue(
                        category=IssueCategory.SCHEMA_MISMATCH,
                        severity=IssueSeverity.ERROR,
                        message=f"Invalid HTTP method: {method}",
                        layer="api",
                        field=ep.get("path", ""),
                        repairable=True,
                        repair_target="api",
                    ))

        return issues

    def _ensure_model(self, layer_name: str, data: Any) -> Any:
        coercers = {
            "intent": coerce_intent,
            "architecture": coerce_architecture,
            "database": coerce_database,
            "api": coerce_api,
            "ui": coerce_ui,
            "auth": coerce_auth,
        }
        coercer = coercers.get(layer_name)
        if coercer and data is not None and isinstance(data, dict):
            return coercer(data)
        return data

    def _missing(self, layer: str, field: str, msg: str | None = None) -> ValidationIssue:
        return ValidationIssue(
            category=IssueCategory.MISSING_FIELD,
            severity=IssueSeverity.ERROR,
            message=msg or f"Missing required field: {field}",
            layer=layer,
            field=field,
            repairable=True,
            repair_target=layer,
        )
