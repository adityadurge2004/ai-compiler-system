"""Error classification for targeted repair."""

from collections import defaultdict

from app.schemas.validation import IssueSeverity, ValidationIssue, ValidationReport

STAGE_MAP = {
    "intent": "intent_extraction",
    "architecture": "architecture_planning",
    "database": "database_generator",
    "api": "api_generator",
    "ui": "ui_generator",
    "auth": "auth_generator",
}


class ErrorClassifier:
    def classify(self, report: ValidationReport) -> dict[str, list[ValidationIssue]]:
        """Group repairable errors by target layer."""
        grouped: dict[str, list[ValidationIssue]] = defaultdict(list)
        for issue in report.issues:
            if issue.severity != IssueSeverity.ERROR:
                continue
            if not issue.repairable:
                continue
            target = issue.repair_target or issue.layer
            if target:
                grouped[target].append(issue)
        return dict(grouped)

    def get_repair_order(self, grouped: dict[str, list[ValidationIssue]]) -> list[str]:
        """Deterministic repair order: foundational layers first."""
        order = ["intent", "architecture", "database", "api", "ui", "auth"]
        return [layer for layer in order if layer in grouped]

    def stage_name_for_layer(self, layer: str) -> str:
        return STAGE_MAP.get(layer, layer)
