"""Runtime Generator - orchestrates all artifact generators."""

from app.schemas.api import ApiSchema
from app.schemas.database import DatabaseSchema
from app.schemas.pipeline import RuntimeArtifacts
from app.schemas.ui import UiSchema
from app.utils.coerce import coerce_api, coerce_database, coerce_ui
from app.runtime.fastapi_generator import FastAPIGenerator
from app.runtime.react_generator import ReactGenerator
from app.runtime.sqlalchemy_generator import SQLAlchemyGenerator
from app.runtime.sqlite_generator import SQLiteGenerator


class RuntimeGenerator:
    def __init__(self) -> None:
        self.sqlite = SQLiteGenerator()
        self.sqlalchemy = SQLAlchemyGenerator()
        self.fastapi = FastAPIGenerator()
        self.react = ReactGenerator()

    def generate(
        self,
        database: DatabaseSchema | dict,
        api: ApiSchema | dict,
        ui: UiSchema | dict,
    ) -> RuntimeArtifacts:
        db = coerce_database(database)
        api_schema = coerce_api(api)
        ui_schema = coerce_ui(ui)
        if not db or not api_schema or not ui_schema:
            raise ValueError("database, api, and ui are required for runtime generation")
        return RuntimeArtifacts(
            sqlite_schema=self.sqlite.generate(db),
            sqlalchemy_models=self.sqlalchemy.generate(db),
            fastapi_routes=self.fastapi.generate(api_schema, db),
            react_form_configs=self.react.generate(ui_schema),
        )
