"""React form configs generator."""

import json

from app.schemas.ui import UiSchema


class ReactGenerator:
    def generate(self, ui: UiSchema) -> str:
        config = {
            "theme": ui.theme,
            "pages": [],
            "globalComponents": [],
        }
        for page in ui.pages:
            page_config = {
                "name": page.name,
                "route": page.route,
                "layout": page.layout,
                "components": [c.model_dump() for c in page.components],
                "forms": [
                    {
                        "name": f.name,
                        "fields": [fld.model_dump() for fld in f.fields],
                        "submitEndpoint": f.submit_endpoint,
                    }
                    for f in page.forms
                ],
                "apiBindings": page.api_bindings,
            }
            config["pages"].append(page_config)
        config["globalComponents"] = [c.model_dump() for c in ui.global_components]

        ts_content = (
            "// Auto-generated React form configs\n"
            "export const appConfig = "
            + json.dumps(config, indent=2)
            + " as const;\n\n"
            "export type AppConfig = typeof appConfig;\n"
        )
        return ts_content
