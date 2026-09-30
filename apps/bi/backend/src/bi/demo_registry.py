"""Small registry backed by synthetic, versioned demo assets."""
from pathlib import Path
import json
from pydantic import BaseModel, Field
from analytics_core.errors import AppError
from analytics_core.mapping.models import ColumnMapping

DEMO_ROOT = Path(__file__).resolve().parents[2] / "demo_data"


class DemoSummary(BaseModel):
    id: str
    name: str
    industry_id: str
    description: str


class DemoDefinition(DemoSummary):
    preset_mapping: list[ColumnMapping] = Field(default_factory=list)


class DemoRegistry:
    def __init__(self, root=DEMO_ROOT):
        self.root = root
        self._definitions = {}
        for metadata in sorted(root.glob("*/demo.json")):
            definition = DemoDefinition.model_validate_json(metadata.read_text(encoding="utf-8"))
            if definition.id in self._definitions:
                raise ValueError("Duplicate demo ID")
            source = metadata.parent / "data.csv"
            if not source.is_file():
                raise ValueError("Missing demo source")
            self._definitions[definition.id] = (definition, source)

    def list(self):
        return [DemoSummary(**definition.model_dump()) for definition, _ in self._definitions.values()]

    def get(self, demo_id):
        try:
            return self._definitions[demo_id]
        except KeyError as exc:
            raise AppError(code="DEMO_NOT_FOUND", http_status=404, message="La demo no existe.") from exc
