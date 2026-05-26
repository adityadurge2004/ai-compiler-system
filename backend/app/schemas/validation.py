"""Validation report schemas."""

from enum import Enum
from pydantic import BaseModel, Field


class IssueSeverity(str, Enum):
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


class IssueCategory(str, Enum):
    JSON_VALIDITY = "json_validity"
    MISSING_FIELD = "missing_field"
    SCHEMA_MISMATCH = "schema_mismatch"
    CROSS_LAYER = "cross_layer"
    LOGICAL = "logical"


class ValidationIssue(BaseModel):
    category: IssueCategory
    severity: IssueSeverity
    message: str
    layer: str = ""
    field: str = ""
    related_layers: list[str] = Field(default_factory=list)
    repairable: bool = True
    repair_target: str = ""


class ValidationReport(BaseModel):
    valid: bool = True
    issues: list[ValidationIssue] = Field(default_factory=list)
    error_count: int = 0
    warning_count: int = 0

    def finalize(self) -> "ValidationReport":
        self.error_count = sum(1 for i in self.issues if i.severity == IssueSeverity.ERROR)
        self.warning_count = sum(1 for i in self.issues if i.severity == IssueSeverity.WARNING)
        self.valid = self.error_count == 0
        return self
