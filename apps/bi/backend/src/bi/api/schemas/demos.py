from pydantic import BaseModel
from bi.demo_registry import DemoSummary


class DemoRequest(BaseModel):
    demo_id: str


__all__ = ["DemoRequest", "DemoSummary"]
