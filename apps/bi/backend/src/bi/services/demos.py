"""Demos reuse upload ingestion and mapping validation without bypassing stages."""
from bi.demo_registry import DemoRegistry
from bi.services.datasets import DatasetService
from bi.services.mapping import MappingService


class DemoService:
    def __init__(self, settings):
        self.registry = DemoRegistry()
        self.datasets = DatasetService(settings)
        self.mapping = MappingService(settings)

    def list(self):
        return self.registry.list()

    def create(self, demo_id):
        definition, source = self.registry.get(demo_id)
        with source.open("rb") as stream:
            session = self.datasets.create(stream, "demo.csv", definition.industry_id)
        try:
            if definition.preset_mapping:
                session = self.mapping.save(session.dataset_id, definition.industry_id, definition.preset_mapping)
            session.demo_id = definition.id
            self.datasets.store.save(session)
            return session
        except Exception:
            self.datasets.delete(session.dataset_id)
            raise
