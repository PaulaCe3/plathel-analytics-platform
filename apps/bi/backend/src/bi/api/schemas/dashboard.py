"""Dashboard HTTP request contracts."""

from pydantic import BaseModel

from bi.dashboard.widgets import DashboardRequest, DashboardResponse, FilterOption


class FilterOptionsResponse(BaseModel):
    field: str
    options: list[FilterOption]


__all__ = ["DashboardRequest", "DashboardResponse", "FilterOptionsResponse"]
