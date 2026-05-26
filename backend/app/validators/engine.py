"""Validation Engine - cross-layer consistency checks."""

from app.schemas.api import ApiSchema
from app.schemas.architecture import ArchitectureSchema
from app.schemas.auth import AuthSchema
from app.schemas.database import DatabaseSchema
from app.schemas.intent import IntentSchema
from app.schemas.ui import UiSchema
from app.schemas.validation import (
    IssueCategory,
    IssueSeverity,
    ValidationIssue,
    ValidationReport,
)
from app.utils.coerce import (
    coerce_api,
    coerce_architecture,
    coerce_auth,
    coerce_database,
    coerce_intent,
    coerce_ui,
)
from app.validators.cross_layer import CrossLayerValidator
from app.validators.field_validator import FieldValidator
from app.validators.json_validator import JsonValidator
from app.validators.logical_validator import LogicalValidator


class ValidationEngine:
    """Orchestrates all validators and produces a unified report."""

    def __init__(self) -> None:
        self.json_validator = JsonValidator()
        self.field_validator = FieldValidator()
        self.cross_layer = CrossLayerValidator()
        self.logical = LogicalValidator()

    def validate(
        self,
        intent: IntentSchema | None = None,
        architecture: ArchitectureSchema | None = None,
        database: DatabaseSchema | None = None,
        api: ApiSchema | None = None,
        ui: UiSchema | None = None,
        auth: AuthSchema | None = None,
    ) -> ValidationReport:
        issues: list[ValidationIssue] = []

        intent = coerce_intent(intent)
        architecture = coerce_architecture(architecture)
        database = coerce_database(database)
        api = coerce_api(api)
        ui = coerce_ui(ui)
        auth = coerce_auth(auth)

        layers = {
            "intent": intent,
            "architecture": architecture,
            "database": database,
            "api": api,
            "ui": ui,
            "auth": auth,
        }

        for name, layer in layers.items():
            if layer is None:
                issues.append(ValidationIssue(
                    category=IssueCategory.MISSING_FIELD,
                    severity=IssueSeverity.ERROR,
                    message=f"Missing required layer: {name}",
                    layer=name,
                    repairable=True,
                    repair_target=name,
                ))
                continue
            issues.extend(self.json_validator.validate_layer(name, layer))
            issues.extend(self.field_validator.validate_layer(name, layer))

        if all(layers[k] is not None for k in ["database", "api"]):
            issues.extend(self.cross_layer.validate_db_api(database, api))  # type: ignore

        if all(layers[k] is not None for k in ["api", "ui"]):
            issues.extend(self.cross_layer.validate_api_ui(api, ui))  # type: ignore

        if all(layers[k] is not None for k in ["api", "auth"]):
            issues.extend(self.cross_layer.validate_api_auth(api, auth))  # type: ignore

        if all(layers[k] is not None for k in ["architecture", "ui"]):
            issues.extend(self.cross_layer.validate_arch_ui(architecture, ui))  # type: ignore

        if intent and architecture:
            issues.extend(self.logical.validate_intent_architecture(intent, architecture))

        if intent and auth:
            issues.extend(self.logical.validate_intent_auth(intent, auth))

        return ValidationReport(issues=issues).finalize()
