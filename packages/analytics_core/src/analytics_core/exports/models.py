"""Format-independent data export contracts; no application dependencies."""
from dataclasses import dataclass
from collections.abc import Callable, Iterable, Iterator
from typing import Any, Literal, Protocol
from pydantic import BaseModel, Field
from analytics_core.cleaning.models import TransformationLog
from analytics_core.engine.query import FilterClause


class ExportOptions(BaseModel):
    format: str = Field(default="csv", description="Formato registrado: csv o xlsx.")
    scope: Literal["clean_data", "filtered_data"] = "clean_data"
    filters: list[FilterClause] = Field(default_factory=list)
    headers: Literal["friendly", "original"] = "friendly"
    include_original_columns: bool = False
    include_ignored_columns: bool = False
    include_transformations: bool = True


@dataclass(frozen=True)
class ExportSource:
    headers: tuple[str, ...]
    rows: Callable[[], Iterable[list[Any]]]
    summary: dict[str, Any]
    transformations: TransformationLog
    locale: str = "es-AR"


class Exporter(Protocol):
    format: str
    content_type: str
    def export(self, source: ExportSource, options: ExportOptions) -> Iterator[bytes]: ...
