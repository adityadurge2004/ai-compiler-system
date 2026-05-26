"""JSON validity and schema structure validators."""

import json

from typing import Any

from pydantic import BaseModel

from app.schemas.database import DatabaseSchema
from app.schemas.validation import IssueCategory, IssueSeverity, ValidationIssue
from app.utils.coerce import coerce_database


class JsonValidator:
    def validate_layer(self, layer_name: str, data: BaseModel) -> list[ValidationIssue]:
        issues: list[ValidationIssue] = []
        try:
            dumped = data.model_dump() if hasattr(data, "model_dump") else data
            json.dumps(dumped)
        except (TypeError, ValueError) as e:
            issues.append(ValidationIssue(
                category=IssueCategory.JSON_VALIDITY,
                severity=IssueSeverity.ERROR,
                message=f"Layer {layer_name} is not JSON-serializable: {e}",
                layer=layer_name,
                repairable=True,
                repair_target=layer_name,
            ))
            return issues

        if layer_name == "database":
            db = coerce_database(data) if not isinstance(data, DatabaseSchema) else data
            if db is not None and not db.tables:
                issues.append(ValidationIssue(
                    category=IssueCategory.MISSING_FIELD,
                    severity=IssueSeverity.ERROR,
                    message="Database schema has no tables",
                    layer=layer_name,
                    field="tables",
                    repairable=True,
                    repair_target="database",
                ))

        if layer_name == "api":
            api = data
            if hasattr(api, "endpoints") and not api.endpoints:
                issues.append(ValidationIssue(
                    category=IssueCategory.MISSING_FIELD,
                    severity=IssueSeverity.ERROR,
                    message="API schema has no endpoints",
                    layer=layer_name,
                    field="endpoints",
                    repairable=True,
                    repair_target="api",
                ))

        return issues
