"""FastAPI CRUD routes generator."""

from app.schemas.api import ApiSchema
from app.schemas.database import DatabaseSchema


class FastAPIGenerator:
    def generate(self, api: ApiSchema, database: DatabaseSchema) -> str:
        lines = [
            '"""Auto-generated FastAPI routes."""',
            "from typing import Any",
            "from fastapi import APIRouter, Depends, HTTPException",
            "from pydantic import BaseModel",
            "",
            "router = APIRouter()",
            "",
        ]

        for ep in api.endpoints:
            route_name = ep.path.replace("/", "_").strip("_").replace("-", "_")
            method_lower = ep.method.lower()
            lines.extend(self._endpoint_block(ep, route_name, method_lower))

        return "\n".join(lines)

    def _endpoint_block(self, ep, route_name: str, method: str) -> list[str]:
        req_fields = ep.request_fields
        if req_fields:
            field_lines = [f"    {f.name}: {self._py_type(f.type)}" + (" | None = None" if not f.required else "") for f in req_fields]
            model = f"class {route_name.title().replace('_', '')}Request(BaseModel):\n" + "\n".join(field_lines)
        else:
            model = ""

        handler = [
            model,
            "",
            f'@router.{method}("{ep.path}")',
            f"async def {route_name}_{method}(request: dict[str, Any] | None = None) -> dict[str, Any]:",
            f'    """{ep.summary or route_name}"""',
        ]
        if ep.auth_required:
            handler.append("    # TODO: inject auth dependency")
        handler.append(f'    return {{"status": "ok", "endpoint": "{ep.path}", "method": "{ep.method.upper()}"}}')
        handler.append("")
        return handler

    def _py_type(self, t: str) -> str:
        return {"string": "str", "integer": "int", "boolean": "bool", "array": "list", "object": "dict"}.get(t, "str")
