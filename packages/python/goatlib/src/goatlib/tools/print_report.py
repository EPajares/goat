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
    access_token: str | None = Field(
        default=None,
        description="Access token for API authentication (passed by GeoAPI)",
        json_schema_extra={"x-ui": {"hidden": True}},
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
                    "--no-sandbox",
                    "--disable-setuid-sandbox",
                    "--disable-dev-shm-usage",
                    # Enable WebGL for MapLibre (software rendering)
                    "--enable-unsafe-swiftshader",
                    "--use-gl=swiftshader",
                    "--use-angle=swiftshader",
                    "--ignore-gpu-blocklist",
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

        # Use the public /print route that doesn't require authentication
        url = f"{base_url}/print/{params.project_id}/{params.layout_id}"

        if page_index is not None:
            url += f"?page={page_index}"

        return url

    async def _render_page(
        self: Self,
        url: str,
        output_format: Literal["pdf", "png"],
        access_token: str | None = None,
    ) -> bytes:
        """Render a single page to PDF or PNG."""
        browser = await self._get_browser()
        context = await browser.new_context(
            viewport={"width": 1920, "height": 1080},
            device_scale_factor=2,  # Higher quality
        )
        page = await context.new_page()

        # Capture console logs for debugging
        page.on(
            "console",
            lambda msg: logger.info(f"Browser console [{msg.type}]: {msg.text}"),
        )
        page.on("pageerror", lambda exc: logger.error(f"Browser page error: {exc}"))

        try:
            # First navigate to the base URL to set localStorage for auth token
            base_url = os.environ.get("PRINT_BASE_URL", "http://localhost:3000")
            logger.info(f"Navigating to base URL first: {base_url}/print")
            await page.goto(
                f"{base_url}/print", wait_until="domcontentloaded", timeout=10000
            )

            # Inject access token into localStorage for API authentication
            if access_token:
                await page.evaluate(
                    f"localStorage.setItem('print_access_token', '{access_token}')"
                )
                logger.info("Injected access token into localStorage")

            # Now navigate to the actual print page
            logger.info(f"Navigating to print page: {url}")
            await page.goto(url, wait_until="networkidle", timeout=DEFAULT_PAGE_TIMEOUT)

            # Wait for the page to signal it's ready
            # The print page sets data-print-ready="true" when all elements are loaded
            try:
                await page.wait_for_selector(
                    "[data-print-ready='true']",
                    state="attached",
                    timeout=DEFAULT_RENDER_TIMEOUT,
                )
                logger.info("Page signaled ready via data-print-ready")
            except Exception as e:
                # Fallback: page didn't signal ready, check if critical elements exist
                logger.warning(
                    f"data-print-ready timeout ({DEFAULT_RENDER_TIMEOUT}ms): {e}"
                )

                # Check for the print paper element (always present)
                paper = await page.query_selector("#print-paper")
                if not paper:
                    raise RuntimeError(
                        "Print paper element not found - page failed to load"
                    )

                logger.info("Print paper found, proceeding with render")

            # Wait for network to be idle (images, tiles, fonts, etc.)
            await page.wait_for_load_state("networkidle", timeout=30000)
            logger.info("Network idle")

            # Small buffer for any final CSS/layout calculations
            await asyncio.sleep(0.5)

            # Get page dimensions from metadata element
            metadata = await page.query_selector("#print-metadata")
            if metadata:
                width_mm = await metadata.get_attribute("data-width-mm") or "210"
                height_mm = await metadata.get_attribute("data-height-mm") or "297"
            else:
                width_mm = "210"
                height_mm = "297"

            if output_format == "pdf":
                # Generate PDF with actual page dimensions
                pdf_bytes = await page.pdf(
                    width=f"{width_mm}mm",
                    height=f"{height_mm}mm",
                    print_background=True,
                    margin={
                        "top": "0mm",
                        "right": "0mm",
                        "bottom": "0mm",
                        "left": "0mm",
                    },
                )
                return pdf_bytes
            else:
                # Capture the print paper area as PNG
                paper_element = await page.query_selector("#print-paper")
                if paper_element:
                    png_bytes = await paper_element.screenshot(type="png")
                else:
                    png_bytes = await page.screenshot(type="png", full_page=True)
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
                    tasks.append(
                        self._render_page(url, params.format, params.access_token)
                    )

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
    runner.init_from_env()  # Configure logging for Windmill
    result = runner.run(params)
    return result.model_dump()
