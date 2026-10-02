"""Demos reuse upload ingestion and mapping validation without bypassing stages."""
from bi.demo_registry import DemoRegistry
from bi.services.datasets import DatasetService
from bi.services.mapping import MappingService
from bi.services.prepare import PrepareService


class DemoService:
    def __init__(self, settings, runtime=None, client_ip="local"):
        self.registry = DemoRegistry()
        self.datasets = DatasetService(settings, runtime, client_ip)
        self.mapping = MappingService(settings)
        self.prepare = PrepareService(settings)
        self.prepare.runtime = runtime

    def list(self):
        return self.registry.list()

    def create(self, demo_id):
        definition, source = self.registry.get(demo_id)
        with source.open("rb") as stream:
            session = self.datasets.create(stream, "demo.csv", definition.industry_id)
        try:
            if definition.preset_mapping:
                session = self.mapping.save(session.dataset_id, definition.industry_id, definition.preset_mapping)
            session, validation, _quality = self.prepare.validate(session.dataset_id)
            if not validation.valid:
                raise ValueError("Invalid demo preset")
            safe_actions = [
                action
                for action in (session.cleaning_plan.actions if session.cleaning_plan else [])
                if action.selected and not action.destructive
            ]
            session, _quality = self.prepare.clean(session.dataset_id, safe_actions)
            session.demo_id = definition.id
            self.datasets.store.save(session)
            return session
        except Exception:
            self.datasets.delete(session.dataset_id)
            raise
