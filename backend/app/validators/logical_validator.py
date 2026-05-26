"""Logical inconsistency validators."""

from app.schemas.architecture import ArchitectureSchema
from app.schemas.auth import AuthSchema
from app.schemas.intent import IntentSchema
from app.schemas.validation import IssueCategory, IssueSeverity, ValidationIssue


class LogicalValidator:
    def validate_intent_architecture(
        self, intent: IntentSchema, architecture: ArchitectureSchema
    ) -> list[ValidationIssue]:
        issues: list[ValidationIssue] = []
        features_lower = [f.lower() for f in intent.features]

        if any("auth" in f or "login" in f for f in features_lower):
            has_login = any("login" in p.name.lower() or "auth" in p.route.lower() for p in architecture.pages)
            if not has_login:
                issues.append(ValidationIssue(
                    category=IssueCategory.LOGICAL,
                    severity=IssueSeverity.WARNING,
                    message="Authentication feature requested but no login page in architecture",
                    layer="architecture",
                    related_layers=["intent"],
                    repairable=True,
                    repair_target="architecture",
                ))

        if any("payment" in f or "stripe" in f for f in features_lower):
            payment_entities = [e for e in architecture.entities if "payment" in e.lower() or "subscription" in e.lower()]
            if not payment_entities:
                issues.append(ValidationIssue(
                    category=IssueCategory.LOGICAL,
                    severity=IssueSeverity.WARNING,
                    message="Payments feature requested but no payment entity in architecture",
                    layer="architecture",
                    related_layers=["intent"],
                    repairable=True,
                    repair_target="architecture",
                ))

        return issues

    def validate_intent_auth(self, intent: IntentSchema, auth: AuthSchema) -> list[ValidationIssue]:
        issues: list[ValidationIssue] = []
        intent_roles = {r.lower() for r in intent.roles}
        auth_roles = {r.name.lower() for r in auth.roles}

        for role in intent_roles:
            if role not in auth_roles:
                issues.append(ValidationIssue(
                    category=IssueCategory.LOGICAL,
                    severity=IssueSeverity.ERROR,
                    message=f"Intent role '{role}' not defined in auth schema",
                    layer="auth",
                    field=role,
                    related_layers=["intent"],
                    repairable=True,
                    repair_target="auth",
                ))

        return issues
