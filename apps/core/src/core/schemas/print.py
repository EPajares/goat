"""Print Report Schemas"""

from enum import Enum
from typing import List
from uuid import UUID

from pydantic import BaseModel, Field


class PrintFormat(str, Enum):
    """Supported print output formats."""

    pdf = "pdf"
    png = "png"


class PrintPageSize(str, Enum):
    """Standard page sizes."""

    A4 = "A4"
    A3 = "A3"
    Letter = "Letter"
    Legal = "Legal"
    Tabloid = "Tabloid"
    Custom = "Custom"


class PrintOrientation(str, Enum):
    """Page orientation."""

    portrait = "portrait"
    landscape = "landscape"


class PrintReportRequest(BaseModel):
    """Request schema for print report job."""

    layout_id: UUID = Field(..., description="ID of the report layout to print")
    format: PrintFormat = Field(
        default=PrintFormat.pdf, description="Output format (pdf or png)"
    )
    # Optional: Override page settings from layout
    page_size: PrintPageSize | None = Field(
        default=None, description="Override page size"
    )
    orientation: PrintOrientation | None = Field(
        default=None, description="Override page orientation"
    )
    # Atlas options
    atlas_page_indices: List[int] | None = Field(
        default=None,
        description="Specific atlas pages to print (0-indexed). If None, prints all pages.",
    )


class PrintReportResult(BaseModel):
    """Result schema for completed print job."""

    download_url: str = Field(..., description="URL to download the generated file")
    file_name: str = Field(..., description="Name of the generated file")
    file_size_bytes: int = Field(..., description="Size of the file in bytes")
    page_count: int = Field(default=1, description="Number of pages generated")
    format: PrintFormat = Field(..., description="Output format")


# Request examples for OpenAPI documentation
request_examples = {
    "print_single": {
        "layout_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
        "format": "pdf",
    },
    "print_atlas_specific_pages": {
        "layout_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
        "format": "pdf",
        "atlas_page_indices": [0, 1, 2],
    },
}
