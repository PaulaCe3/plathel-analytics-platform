"""Register another exporter without changing endpoint dispatch."""
from analytics_core.errors import AppError
from analytics_core.exports.csv import CSVExporter
from analytics_core.exports.xlsx import XLSXExporter


class ExporterRegistry:
    def __init__(self):
        self._exporters = {}

    def register(self, exporter):
        if exporter.format in self._exporters:
            raise ValueError("Duplicate export format")
        self._exporters[exporter.format] = exporter

    def get(self, format):
        if format not in self._exporters:
            raise AppError(code="EXPORT_FORMAT_UNSUPPORTED", http_status=422, message="El formato de exportación no está disponible.")
        return self._exporters[format]


def build_exporter_registry():
    registry = ExporterRegistry()
    registry.register(CSVExporter())
    registry.register(XLSXExporter())
    return registry
