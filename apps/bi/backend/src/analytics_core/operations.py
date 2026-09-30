"""Shared heavy-operation guard and privacy-safe stage timing."""
from contextlib import nullcontext
from functools import wraps
from analytics_core.logging import timed


def heavy_operation(function):
    @wraps(function)
    def guarded(self, *args, **kwargs):
        runtime = getattr(self, "runtime", None)
        with runtime.heavy() if runtime else nullcontext():
            return function(self, *args, **kwargs)
    return guarded


def stage(name):
    def decorate(function):
        @wraps(function)
        def measured(*args, **kwargs):
            with timed(name) as counts:
                result = function(*args, **kwargs)
                counts["rows"] = getattr(result, "row_count", None)
                counts["columns"] = getattr(result, "column_count", None)
                if counts["columns"] is None and hasattr(result, "columns"): counts["columns"] = len(result.columns)
                return result
        return measured
    return decorate


def session_operation(function):
    """Avoid concurrent mutation/deletion of the same temporary session."""
    @wraps(function)
    def guarded(self, dataset_id, *args, **kwargs):
        store = getattr(self, "store", self)
        with store.lock(dataset_id):
            try:
                return function(self, dataset_id, *args, **kwargs)
            except OSError as exc:
                from analytics_core.errors import AppError
                raise AppError(code="STORAGE_UNAVAILABLE", http_status=503, message="Los datos temporales no están disponibles. Intentá nuevamente.") from exc
    return guarded
