"""
Report Layout Schemas
"""

from typing import Any, Dict
from uuid import UUID

from pydantic import BaseModel, Field


class ReportLayoutBase(BaseModel):
    """Base schema for report layout."""

    name: str = Field(..., description="Layout name", max_length=255)
    description: str | None = Field(None, description="Layout description")
    is_default: bool = Field(False, description="Whether this is the default layout")
    config: Dict[str, Any] = Field(
        ...,
        description="Layout configuration (page setup, elements, theme, etc.)",
    )


class ReportLayoutCreate(ReportLayoutBase):
    """Schema for creating a report layout."""

    pass


class ReportLayoutUpdate(BaseModel):
    """Schema for updating a report layout."""

    name: str | None = Field(None, description="Layout name", max_length=255)
    description: str | None = Field(None, description="Layout description")
    is_default: bool | None = Field(
        None, description="Whether this is the default layout"
    )
    config: Dict[str, Any] | None = Field(
        None,
        description="Layout configuration (page setup, elements, theme, etc.)",
    )


class ReportLayoutRead(ReportLayoutBase):
    """Schema for reading a report layout."""

    id: UUID = Field(..., description="Layout ID")
    project_id: UUID = Field(..., description="Parent project ID")
    is_predefined: bool = Field(False, description="System-provided predefined layout")
    thumbnail_url: str | None = Field(None, description="Layout preview thumbnail URL")

    class Config:
        from_attributes = True


# Request examples for OpenAPI documentation
request_examples = {
    "create": {
        "name": "Summary Report",
        "description": "A summary report for the project",
        "is_default": True,
        "config": {
            "page": {
                "size": "A4",
                "orientation": "portrait",
                "margins": {"top": 10, "right": 10, "bottom": 10, "left": 10},
            },
            "layout": {"type": "grid", "columns": 12, "rows": 12, "gap": 5},
            "elements": [],
            "theme": None,
            "atlas": None,
        },
    },
    "update": {
        "name": "Updated Report Name",
        "config": {
            "page": {
                "size": "A3",
                "orientation": "landscape",
                "margins": {"top": 15, "right": 15, "bottom": 15, "left": 15},
            },
            "layout": {"type": "grid", "columns": 12, "rows": 12, "gap": 5},
            "elements": [],
            "theme": None,
            "atlas": None,
        },
    },
}
