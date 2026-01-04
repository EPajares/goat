"""PrintReport Tool - Generate PDF/PNG reports from map layouts.

This tool uses Playwright to render map layouts in a headless browser,
generating PDF or PNG exports. Supports atlas mode for multi-page reports.

The generated files are uploaded to S3 and a presigned download URL is returned.

Usage:
    from goatlib.tools.print_report import PrintReportParams, main

    result = main(PrintReportParams(
        user_id="...",
        project_id="...",
        layout_id="...",
        format="pdf",
    ))
"""

import asyncio
import io
import logging
import os
import zipfile
from datetime import datetime
from typing import Literal, Self

from pydantic import BaseModel, ConfigDict, Field

from goatlib.tools.base import SimpleToolRunner
from goatlib.tools.schemas import ToolInputBase

logger = logging.getLogger(__name__)

# Default timeouts
DEFAULT_PAGE_TIMEOUT = 60000  # 60 seconds
DEFAULT_RENDER_TIMEOUT = 30000  # 30 seconds

# Batch size for parallel atlas rendering
ATLAS_BATCH_SIZE = 5


class PrintReportParams(ToolInputBase):
    """Parameters for PrintReport tool."""

    model_config = ConfigDict(
        json_schema_extra={
            "x-ui-sections": [
                {"id": "input", "order": 1},
                {"id": "output", "order": 2},
            ]
        }
    )

    project_id: str = Field(
        ...,
        description="ID of the project containing the report layout",
        json_schema_extra={
            "x-ui": {"section": "input", "field_order": 1, "hidden": True}
        },
    )
    layout_id: str = Field(
        ...,
        description="ID of the report layout to print",
        json_schema_extra={
            "x-ui": {"section": "input", "field_order": 2, "hidden": True}
        },
    )
    format: Literal["pdf", "png"] = Field(
        default="pdf",
        description="Output format (pdf or png)",
        json_schema_extra={
            "x-ui": {
                "section": "output",
                "field_order": 1,
                "widget": "select",
                "widget_options": {
                    "options": [
                        {"value": "pdf", "label": "PDF"},
                        {"value": "png", "label": "PNG"},
                    ]
                },
            }
        },
    )
    total_atlas_pages: int = Field(
        default=1,
        description="Total number of atlas pages to render. Ignored if atlas_page_indices is provided.",
        json_schema_extra={
            "x-ui": {"section": "output", "field_order": 2, "hidden": True}
        },
    )
    atlas_page_indices: list[int] | None = Field(
        default=None,
        description="Specific atlas page indices to render (0-based). Overrides total_atlas_pages.",
        json_schema_extra={
            "x-ui": {"section": "output", "field_order": 3, "hidden": True}
        },
    )


class PrintReportOutput(BaseModel):
    """Output from PrintReport tool.

    Note: Does NOT inherit from ToolOutputBase since PrintReport
    creates a downloadable file, not a layer.
    """

    download_url: str = Field(..., description="Presigned URL to download the report")
    file_name: str = Field(..., description="Name of the generated file")
    format: str = Field(..., description="Output format (pdf or png)")
    page_count: int = Field(default=1, description="Number of pages/images generated")


class PrintReportRunner(SimpleToolRunner):
    """Runner for PrintReport tool using Playwright."""

    def __init__(self: Self) -> None:
        super().__init__()
        self._browser = None
        self._playwright = None

    async def _get_browser(self: Self):  # noqa: ANN202
        """Get or create Playwright browser instance."""
        if self._browser is None:
            from playwright.async_api import async_playwright

            self._playwright = await async_playwright().start()
            self._browser = await self._playwright.chromium.launch(
                headless=True,
                args=[
                    "--disable-gpu",
                    "--disable-dev-shm-usage",
                    "--disable-setuid-sandbox",
                    "--no-sandbox",
                ],
            )
        return self._browser

    async def _close_browser(self: Self) -> None:
        """Close browser and playwright instances."""
        if self._browser:
            await self._browser.close()
            self._browser = None
        if self._playwright:
            await self._playwright.stop()
            self._playwright = None

    def _get_report_url(
        self: Self, params: PrintReportParams, page_index: int | None = None
    ) -> str:
        """Build the report preview URL."""
        # Get base URL from environment (set via Windmill workspace env vars)
        base_url = os.environ.get("PRINT_BASE_URL", "http://goat-web:3000")

        url = f"{base_url}/projects/{params.project_id}/reports/{params.layout_id}/preview"

        if page_index is not None:
            url += f"?atlasPageIndex={page_index}"

        return url

    async def _render_page(
        self: Self,
        url: str,
        output_format: Literal["pdf", "png"],
        page_width: int = 1200,
        page_height: int = 1697,  # A4 ratio
    ) -> bytes:
        """Render a single page to PDF or PNG."""
        browser = await self._get_browser()
        context = await browser.new_context(
            viewport={"width": page_width, "height": page_height},
            device_scale_factor=2,  # Higher quality
        )
        page = await context.new_page()

        try:
            # Navigate to the report preview
            await page.goto(url, wait_until="networkidle", timeout=DEFAULT_PAGE_TIMEOUT)

            # Wait for the report to be fully rendered
            # Look for a specific element that indicates the report is ready
            try:
                await page.wait_for_selector(
                    "[data-report-ready='true']", timeout=DEFAULT_RENDER_TIMEOUT
                )
            except Exception:
                # Fallback: wait for network idle and a short delay
                await page.wait_for_load_state("networkidle")
                await asyncio.sleep(2)

            if output_format == "pdf":
                # Generate PDF
                pdf_bytes = await page.pdf(
                    format="A4",
                    print_background=True,
                    margin={"top": "0", "right": "0", "bottom": "0", "left": "0"},
                )
                return pdf_bytes
            else:
                # Generate PNG screenshot
                png_bytes = await page.screenshot(
                    type="png",
                    full_page=True,
                )
                return png_bytes

        finally:
            await context.close()

    async def _merge_pdfs(self: Self, pdf_list: list[bytes]) -> bytes:
        """Merge multiple PDFs into one."""
        from pypdf import PdfReader, PdfWriter

        writer = PdfWriter()

        for pdf_bytes in pdf_list:
            reader = PdfReader(io.BytesIO(pdf_bytes))
            for page in reader.pages:
                writer.add_page(page)

        output = io.BytesIO()
        writer.write(output)
        return output.getvalue()

    async def run_async(self: Self, params: PrintReportParams) -> PrintReportOutput:
        """Execute the print report job."""
        from goatlib.services.s3 import S3Service

        try:
            # Determine pages to render
            if params.atlas_page_indices is not None:
                # Specific pages requested
                page_indices = params.atlas_page_indices
            elif params.total_atlas_pages > 1:
                # Render all atlas pages
                page_indices = list(range(params.total_atlas_pages))
            else:
                # Single page (no atlas or atlas with 1 page)
                page_indices = [None]

            logger.info(
                f"Rendering {len(page_indices)} pages in {params.format} format"
            )

            # Render pages in batches
            rendered_pages: list[bytes] = []

            for i in range(0, len(page_indices), ATLAS_BATCH_SIZE):
                batch = page_indices[i : i + ATLAS_BATCH_SIZE]
                tasks = []

                for page_idx in batch:
                    url = self._get_report_url(params, page_idx)
                    tasks.append(self._render_page(url, params.format))

                batch_results = await asyncio.gather(*tasks)
                rendered_pages.extend(batch_results)
                logger.info(f"Rendered batch {i // ATLAS_BATCH_SIZE + 1}")

            # Generate output file
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

            if params.format == "pdf":
                if len(rendered_pages) > 1:
                    # Merge PDFs
                    output_bytes = await self._merge_pdfs(rendered_pages)
                else:
                    output_bytes = rendered_pages[0]

                file_name = f"report_{params.layout_id}_{timestamp}.pdf"
                content_type = "application/pdf"

            else:  # PNG
                if len(rendered_pages) > 1:
                    # Create ZIP of PNGs
                    zip_buffer = io.BytesIO()
                    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
                        for idx, png_bytes in enumerate(rendered_pages):
                            zf.writestr(f"page_{idx + 1:03d}.png", png_bytes)
                    output_bytes = zip_buffer.getvalue()
                    file_name = f"report_{params.layout_id}_{timestamp}.zip"
                    content_type = "application/zip"
                else:
                    output_bytes = rendered_pages[0]
                    file_name = f"report_{params.layout_id}_{timestamp}.png"
                    content_type = "image/png"

            # Upload to S3
            s3_service = S3Service()
            s3_key = f"exports/{params.user_id}/reports/{file_name}"

            s3_service.upload_file(
                io.BytesIO(output_bytes),
                s3_key,
                content_type=content_type,
            )

            # Generate presigned download URL
            download_url = s3_service.generate_presigned_get(
                s3_key, expires_in=86400
            )  # 24 hours

            return PrintReportOutput(
                download_url=download_url,
                file_name=file_name,
                format=params.format,
                page_count=len(rendered_pages),
            )

        finally:
            await self._close_browser()

    def run(self: Self, params: PrintReportParams) -> PrintReportOutput:
        """Synchronous wrapper for run_async."""
        return asyncio.run(self.run_async(params))


def main(params: PrintReportParams) -> dict:
    """Entry point for Windmill."""
    runner = PrintReportRunner()
    result = runner.run(params)
    return result.model_dump()
