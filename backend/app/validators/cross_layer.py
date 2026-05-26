"""Cross-layer consistency validators."""

import re

from app.schemas.api import ApiSchema
from app.schemas.architecture import ArchitectureSchema
from app.schemas.auth import AuthSchema
from app.schemas.database import DatabaseSchema
from app.schemas.ui import UiSchema
from app.schemas.validation import IssueCategory, IssueSeverity, ValidationIssue
from app.utils.coerce import coerce_database


def _normalize(name: str) -> str:
    return re.sub(r"[^a-z0-9]", "", name.lower())


def _table_fields(db: DatabaseSchema | dict) -> dict[str, set[str]]:
    schema = coerce_database(db)
    if schema is None:
        return {}
    result: dict[str, set[str]] = {}
    for table in schema.tables:
        result[_normalize(table.name)] = {_normalize(f.name) for f in table.fields}
    return result


def _resource_from_path(path: str) -> str:
    parts = [p for p in path.strip("/").split("/") if p and p != "api" and not p.startswith("v")]
    return _normalize(parts[-1] if parts else path)


class CrossLayerValidator:
    def validate_db_api(self, db: DatabaseSchema, api: ApiSchema) -> list[ValidationIssue]:
        issues: list[ValidationIssue] = []
        tables = _table_fields(db)
        table_names = set(tables.keys())

        for ep in api.endpoints:
            resource = _resource_from_path(ep.path)
            if resource in ("auth", "login", "register", "health"):
                continue
            singular = resource.rstrip("s") if resource.endswith("s") else resource
            matched = resource in table_names or singular in table_names
            if not matched and table_names:
                issues.append(ValidationIssue(
                    category=IssueCategory.CROSS_LAYER,
                    severity=IssueSeverity.WARNING,
                    message=f"API endpoint '{ep.path}' has no matching database table",
                    layer="api",
                    field=ep.path,
                    related_layers=["database"],
                    repairable=True,
                    repair_target="api",
                ))

            for req in ep.request_fields:
                found = False
                for fields in tables.values():
                    if _normalize(req.name) in fields:
                        found = True
                        break
                if not found and req.required and table_names:
                    issues.append(ValidationIssue(
                        category=IssueCategory.CROSS_LAYER,
                        severity=IssueSeverity.ERROR,
                        message=f"API field '{req.name}' on '{ep.path}' not found in any DB table",
                        layer="api",
                        field=req.name,
                        related_layers=["database"],
                        repairable=True,
                        repair_target="api",
                    ))

        return issues

    def validate_api_ui(self, api: ApiSchema, ui: UiSchema) -> list[ValidationIssue]:
        issues: list[ValidationIssue] = []
        api_paths = {ep.path for ep in api.endpoints}
        api_paths_full = {f"{api.base_path}{ep.path}" if not ep.path.startswith(api.base_path) else ep.path for ep in api.endpoints}
        all_paths = api_paths | api_paths_full

        for page in ui.pages:
            for binding in page.api_bindings:
                normalized = binding if binding.startswith("/") else f"{api.base_path}/{binding}"
                if not any(normalized.endswith(p) or p.endswith(normalized.split("/")[-1]) for p in all_paths):
                    if binding not in all_paths:
                        issues.append(ValidationIssue(
                            category=IssueCategory.CROSS_LAYER,
                            severity=IssueSeverity.ERROR,
                            message=f"UI binding '{binding}' on page '{page.name}' not found in API",
                            layer="ui",
                            field=binding,
                            related_layers=["api"],
                            repairable=True,
                            repair_target="ui",
                        ))

            for form in page.forms:
                if form.submit_endpoint and form.submit_endpoint not in all_paths:
                    match = any(form.submit_endpoint.endswith(ep.path) for ep in api.endpoints)
                    if not match:
                        issues.append(ValidationIssue(
                            category=IssueCategory.CROSS_LAYER,
                            severity=IssueSeverity.WARNING,
                            message=f"Form submit endpoint '{form.submit_endpoint}' may not match API",
                            layer="ui",
                            field=form.submit_endpoint,
                            related_layers=["api"],
                            repairable=True,
                            repair_target="ui",
                        ))

                for field in form.fields:
                    if not field.api_binding:
                        continue
                    found = False
                    for ep in api.endpoints:
                        req_names = {_normalize(r.name) for r in ep.request_fields}
                        if _normalize(field.api_binding) in req_names:
                            found = True
                            break
                    if not found:
                        issues.append(ValidationIssue(
                            category=IssueCategory.CROSS_LAYER,
                            severity=IssueSeverity.ERROR,
                            message=f"UI field '{field.name}' api_binding '{field.api_binding}' not in API request schemas",
                            layer="ui",
                            field=field.api_binding,
                            related_layers=["api"],
                            repairable=True,
                            repair_target="ui",
                        ))

        return issues

    def validate_api_auth(self, api: ApiSchema, auth: AuthSchema) -> list[ValidationIssue]:
        issues: list[ValidationIssue] = []
        role_names = {_normalize(r.name) for r in auth.roles}

        for ep in api.endpoints:
            if ep.auth_required:
                for role in ep.roles:
                    if _normalize(role) not in role_names:
                        issues.append(ValidationIssue(
                            category=IssueCategory.CROSS_LAYER,
                            severity=IssueSeverity.ERROR,
                            message=f"API endpoint '{ep.path}' references unknown role '{role}'",
                            layer="api",
                            field=role,
                            related_layers=["auth"],
                            repairable=True,
                            repair_target="auth",
                        ))

        return issues

    def validate_arch_ui(self, arch: ArchitectureSchema, ui: UiSchema) -> list[ValidationIssue]:
        issues: list[ValidationIssue] = []
        arch_pages = {_normalize(p.name) for p in arch.pages}
        ui_pages = {_normalize(p.name) for p in ui.pages}

        for ap in arch_pages:
            if ap not in ui_pages:
                issues.append(ValidationIssue(
                    category=IssueCategory.CROSS_LAYER,
                    severity=IssueSeverity.WARNING,
                    message=f"Architecture page '{ap}' missing from UI schema",
                    layer="ui",
                    field=ap,
                    related_layers=["architecture"],
                    repairable=True,
                    repair_target="ui",
                ))

        return issues
