"""
PrintReport Generate Step - Event Handler

Subscribes to print-requested events and generates PDF/PNG using Playwright.
Uploads result to S3 and emits job completion event.

Topics: print-requested -> job.completed / job.failed
"""

import sys

sys.path.insert(0, "/app/apps/processes/src")  # noqa: E702
import asyncio
import io
import logging
import re
import zipfile
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

import lib.paths  # noqa: F401 - sets up remaining paths
from lib.config import get_settings
from lib.job_state import job_state_manager
from lib.s3 import S3Service, get_s3_service
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class PrintRequestInput(BaseModel):
    """Input schema for print-requested event."""

    job_id: str = Field(..., description="Job UUID for tracking")
    user_id: str = Field(..., description="User UUID (requester)")
    access_token: str = Field(..., description="Access token for API auth")
    project_id: str = Field(..., description="Project UUID")
    layout_id: str = Field(..., description="Report layout UUID")
    format: str = Field(default="pdf", description="Output format: pdf or png")
    atlas_page_indices: Optional[List[int]] = Field(
        default=None, description="Atlas page indices to render"
    )
    timestamp: str = Field(..., description="Job creation timestamp")


class PrintResult(BaseModel):
    """Result schema for completed print job."""

    job_id: str
    status: str
    s3_key: Optional[str] = None
    download_url: Optional[str] = None
    file_name: Optional[str] = None
    file_size_bytes: Optional[int] = None
    page_count: Optional[int] = None
    format: Optional[str] = None
    layout_id: Optional[str] = None
    error: Optional[str] = None
    processed_at: str


config = {
    "name": "PrintReportGenerate",
    "type": "event",
    "description": "Generate PDF/PNG from print layout using Playwright",
    "subscribes": ["print-requested"],
    "emits": ["job.completed", "job.failed"],
    "flows": ["print-flow"],
    "input": PrintRequestInput.model_json_schema(),
    "infrastructure": {
        "handler": {
            "timeout": 600  # 10 minutes for large atlas prints
        },
        "queue": {
            "visibilityTimeout": 660  # 600 + 60s buffer
        },
    },
}


def sanitize_filename(name: str) -> str:
    """Sanitize a string to be used as a filename."""
    name = name.replace(" ", "_")
    name = re.sub(r"[^\w\-]", "", name)
    name = re.sub(r"_+", "_", name)
    name = name.strip("_")
    return name or "Report"


class PrintReportGenerator:
    """Generates PDF/PNG reports using Playwright."""

    def __init__(
        self,
        settings,
        s3_service: S3Service,
        logger,
    ) -> None:
        self.settings = settings
        self.s3_service = s3_service
        self.logger = logger

    async def _setup_browser_context(self, playwright):
        """Set up browser and context with WebGL support."""
        browser = await playwright.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-dev-shm-usage",
                # Enable WebGL for MapLibre
                "--use-gl=egl",
                "--ignore-gpu-blocklist",
                "--use-gl=angle",
            ],
        )
        context = await browser.new_context(
            viewport={"width": 1920, "height": 1080},
            device_scale_factor=2,
        )
        return browser, context

    async def _inject_auth_token(self, page, base_url: str, access_token: str):
        """Navigate to base URL and inject auth token into localStorage."""
        await page.goto(
            f"{base_url}/print", wait_until="domcontentloaded", timeout=10000
        )
        if access_token:
            await page.evaluate(
                f'localStorage.setItem("print_access_token", "{access_token}")'
            )

    async def _render_page(
        self,
        page,
        print_url: str,
        atlas_page_index: Optional[int] = None,
        is_first_page: bool = True,
    ) -> Tuple[str, str, int]:
        """Render a single page and return (width_mm, height_mm, total_atlas_pages)."""
        url = print_url
        if atlas_page_index is not None:
            url = f"{print_url}?page={atlas_page_index}"

        timeout_ms = (
            self.settings.PRINT_FIRST_PAGE_TIMEOUT_MS
            if is_first_page
            else self.settings.PRINT_SUBSEQUENT_PAGE_TIMEOUT_MS
        )

        await page.goto(
            url,
            wait_until="networkidle",
            timeout=timeout_ms,
        )

        await page.wait_for_selector(
            '[data-print-ready="true"]',
            state="attached",
            timeout=timeout_ms,
        )

        network_timeout = 30000 if is_first_page else 15000
        await page.wait_for_load_state("networkidle", timeout=network_timeout)

        metadata = await page.query_selector("#print-metadata")
        if metadata:
            width_mm = await metadata.get_attribute("data-width-mm") or "210"
            height_mm = await metadata.get_attribute("data-height-mm") or "297"
            atlas_total = await metadata.get_attribute("data-atlas-total-pages") or "0"
        else:
            width_mm = "210"
            height_mm = "297"
            atlas_total = "0"

        return width_mm, height_mm, int(atlas_total)

    async def _capture_pdf(self, page, width_mm: str, height_mm: str) -> bytes:
        """Capture page as PDF."""
        return await page.pdf(
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

    async def _capture_png(self, page) -> bytes:
        """Capture the print paper area as PNG screenshot."""
        paper_element = await page.query_selector("#print-paper")
        if paper_element:
            return await paper_element.screenshot(type="png")
        else:
            return await page.screenshot(type="png", full_page=True)

    def _merge_pdfs(self, pdf_buffers: List[bytes]) -> bytes:
        """Merge multiple PDF buffers into a single PDF."""
        from pypdf import PdfReader, PdfWriter

        writer = PdfWriter()
        for pdf_bytes in pdf_buffers:
            reader = PdfReader(io.BytesIO(pdf_bytes))
            for pdf_page in reader.pages:
                writer.add_page(pdf_page)

        output = io.BytesIO()
        writer.write(output)
        return output.getvalue()

    def _create_zip(self, images: List[Tuple[str, bytes]]) -> bytes:
        """Create a ZIP file from a list of (filename, bytes) tuples."""
        output = io.BytesIO()
        with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as zf:
            for filename, data in images:
                zf.writestr(filename, data)
        return output.getvalue()

    async def _render_atlas_pdf(
        self,
        page,
        print_url: str,
        page_indices: List[int],
        width_mm: str,
        height_mm: str,
    ) -> bytes:
        """Render atlas pages as PDF in parallel batches and merge them."""
        all_pdfs: List[bytes] = []
        context = page.context
        batch_size = self.settings.PRINT_ATLAS_BATCH_SIZE

        async def render_single_page(idx: int) -> Tuple[int, bytes]:
            new_page = await context.new_page()
            try:
                url = f"{print_url}?page={idx}"
                await new_page.goto(
                    url,
                    wait_until="networkidle",
                    timeout=self.settings.PRINT_SUBSEQUENT_PAGE_TIMEOUT_MS,
                )
                await new_page.wait_for_selector(
                    '[data-print-ready="true"]',
                    state="attached",
                    timeout=self.settings.PRINT_SUBSEQUENT_PAGE_TIMEOUT_MS,
                )
                await new_page.wait_for_load_state("networkidle", timeout=15000)

                pdf_bytes = await new_page.pdf(
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
                return (idx, pdf_bytes)
            finally:
                await new_page.close()

        for batch_start in range(0, len(page_indices), batch_size):
            batch_end = min(batch_start + batch_size, len(page_indices))
            batch_indices = page_indices[batch_start:batch_end]

            self.logger.info(
                f"Processing PDF batch {batch_start // batch_size + 1}: "
                f"pages {batch_indices[0]+1} to {batch_indices[-1]+1} (parallel)"
            )

            tasks = [render_single_page(idx) for idx in batch_indices]
            results = await asyncio.gather(*tasks)

            results_sorted = sorted(results, key=lambda x: x[0])
            for _, pdf_bytes in results_sorted:
                all_pdfs.append(pdf_bytes)

        if len(all_pdfs) == 1:
            return all_pdfs[0]
        return self._merge_pdfs(all_pdfs)

    async def _render_atlas_png_zip(
        self,
        page,
        print_url: str,
        page_indices: List[int],
        layout_name: str,
    ) -> bytes:
        """Render atlas pages as PNG images in parallel batches and create a ZIP file."""
        images: List[Tuple[str, bytes]] = []
        sanitized_name = sanitize_filename(layout_name)
        context = page.context
        batch_size = self.settings.PRINT_ATLAS_BATCH_SIZE

        async def render_single_page(idx: int) -> Tuple[int, str, bytes]:
            new_page = await context.new_page()
            try:
                url = f"{print_url}?page={idx}"
                await new_page.goto(
                    url,
                    wait_until="networkidle",
                    timeout=self.settings.PRINT_SUBSEQUENT_PAGE_TIMEOUT_MS,
                )
                await new_page.wait_for_selector(
                    '[data-print-ready="true"]',
                    state="attached",
                    timeout=self.settings.PRINT_SUBSEQUENT_PAGE_TIMEOUT_MS,
                )
                await new_page.wait_for_load_state("networkidle", timeout=15000)

                png_bytes = await new_page.screenshot(type="png", full_page=True)
                filename = f"{sanitized_name}_{idx + 1:03d}.png"
                return (idx, filename, png_bytes)
            finally:
                await new_page.close()

        for batch_start in range(0, len(page_indices), batch_size):
            batch_end = min(batch_start + batch_size, len(page_indices))
            batch_indices = page_indices[batch_start:batch_end]

            self.logger.info(
                f"Processing PNG batch {batch_start // batch_size + 1}: "
                f"pages {batch_indices[0]+1} to {batch_indices[-1]+1} (parallel)"
            )

            tasks = [render_single_page(idx) for idx in batch_indices]
            results = await asyncio.gather(*tasks)

            results_sorted = sorted(results, key=lambda x: x[0])
            for _, filename, png_bytes in results_sorted:
                images.append((filename, png_bytes))

        return self._create_zip(images)

    async def generate(
        self,
        project_id: str,
        layout_id: str,
        output_format: str,
        access_token: str,
        user_id: str,
        atlas_page_indices: Optional[List[int]] = None,
        layout_name: str = "Report",
    ) -> Dict[str, Any]:
        """Generate PDF/PNG using Playwright, with atlas support."""
        try:
            from playwright.async_api import async_playwright
        except ImportError:
            raise ImportError(
                "Playwright is not installed. "
                "Run: pip install playwright && playwright install chromium"
            )

        base_url = self.settings.PRINT_FRONTEND_URL.rstrip("/")
        print_url = f"{base_url}/print/{project_id}/{layout_id}"

        self.logger.info(f"Generating print from URL: {print_url}")

        async with async_playwright() as p:
            browser, context = await self._setup_browser_context(p)

            try:
                page = await context.new_page()

                # Inject auth token
                await self._inject_auth_token(page, base_url, access_token)

                # First, render page 0 to get atlas info
                width_mm, height_mm, atlas_total_pages = await self._render_page(
                    page, print_url, atlas_page_index=0
                )

                # Determine which pages to render
                if atlas_total_pages > 1:
                    # Atlas mode - determine page indices
                    if atlas_page_indices:
                        page_indices = [
                            i for i in atlas_page_indices if 0 <= i < atlas_total_pages
                        ]
                    else:
                        page_indices = list(range(atlas_total_pages))

                    self.logger.info(
                        f"Atlas mode: {len(page_indices)} pages to render "
                        f"(total: {atlas_total_pages})"
                    )

                    if output_format == "pdf":
                        output_buffer = await self._render_atlas_pdf(
                            page, print_url, page_indices, width_mm, height_mm
                        )
                        page_count = len(page_indices)
                        file_extension = "pdf"
                        content_type = "application/pdf"
                    else:
                        output_buffer = await self._render_atlas_png_zip(
                            page, print_url, page_indices, layout_name
                        )
                        page_count = len(page_indices)
                        file_extension = "zip"
                        content_type = "application/zip"
                else:
                    # Single page mode
                    self.logger.info("Single page mode")
                    page_count = 1

                    if output_format == "pdf":
                        output_buffer = await self._capture_pdf(
                            page, width_mm, height_mm
                        )
                        file_extension = "pdf"
                        content_type = "application/pdf"
                    else:
                        output_buffer = await self._capture_png(page)
                        file_extension = "png"
                        content_type = "image/png"

                await context.close()

            finally:
                await browser.close()

        # Generate filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        sanitized_name = sanitize_filename(layout_name)
        file_name = f"{sanitized_name}_{timestamp}.{file_extension}"

        # S3 key
        s3_key = S3Service.build_s3_key(
            self.settings.S3_BUCKET_PATH or "",
            self.settings.PRINT_OUTPUT_DIR,
            user_id,
            f"{project_id}_{layout_id}_{timestamp}.{file_extension}",
        )

        # Upload to S3
        self.s3_service.upload_file(
            file_content=io.BytesIO(output_buffer),
            bucket_name=self.settings.S3_BUCKET_NAME,
            s3_key=s3_key,
            content_type=content_type,
        )

        # Generate presigned download URL
        download_url = self.s3_service.generate_presigned_download_url(
            bucket_name=self.settings.S3_BUCKET_NAME,
            s3_key=s3_key,
            expires_in=3600,  # 1 hour
            filename=file_name,
        )

        return {
            "s3_key": s3_key,
            "download_url": download_url,
            "file_name": file_name,
            "file_size_bytes": len(output_buffer),
            "page_count": page_count,
            "format": output_format,
            "layout_id": layout_id,
        }


async def handler(input_data: Dict[str, Any], context):
    """Handle print-requested event."""
    job_id = input_data.get("job_id")
    user_id = input_data.get("user_id")
    access_token = input_data.get("access_token")
    project_id = input_data.get("project_id")
    layout_id = input_data.get("layout_id")
    output_format = input_data.get("format", "pdf")
    atlas_page_indices = input_data.get("atlas_page_indices")

    context.logger.info(
        "Starting print generation",
        {
            "job_id": job_id,
            "project_id": project_id,
            "layout_id": layout_id,
            "format": output_format,
        },
    )

    # Update job status to running
    await job_state_manager.update_job_status(
        job_id=job_id,
        status="running",
        message="Generating print output...",
    )

    settings = get_settings()
    s3_service = get_s3_service()

    try:
        generator = PrintReportGenerator(
            settings=settings,
            s3_service=s3_service,
            logger=context.logger,
        )

        # TODO: Fetch layout name from API if needed
        # For now use a placeholder - the frontend handles display names
        layout_name = "Report"

        result = await generator.generate(
            project_id=project_id,
            layout_id=layout_id,
            output_format=output_format,
            access_token=access_token,
            user_id=user_id,
            atlas_page_indices=atlas_page_indices,
            layout_name=layout_name,
        )

        context.logger.info(
            "Print generation completed",
            {
                "job_id": job_id,
                "s3_key": result["s3_key"],
                "file_name": result["file_name"],
                "page_count": result["page_count"],
            },
        )

        # Update job status
        await job_state_manager.update_job_status(
            job_id=job_id,
            status="successful",
            message="Print generation completed",
            progress=100,
        )

        # Emit job completed event
        completed_result = PrintResult(
            job_id=job_id,
            status="successful",
            s3_key=result["s3_key"],
            download_url=result["download_url"],
            file_name=result["file_name"],
            file_size_bytes=result["file_size_bytes"],
            page_count=result["page_count"],
            format=result["format"],
            layout_id=result["layout_id"],
            processed_at=datetime.now(timezone.utc).isoformat(),
        )

        await context.emit(
            {
                "topic": "job.completed",
                "data": {
                    "job_id": job_id,
                    "user_id": user_id,
                    "process_id": "PrintReport",
                    "status": "successful",
                    "result": completed_result.model_dump(),
                },
            }
        )

    except Exception as e:
        error_message = str(e)
        context.logger.error(
            "Print generation failed",
            {"job_id": job_id, "error": error_message},
        )

        # Update job status
        await job_state_manager.update_job_status(
            job_id=job_id,
            status="failed",
            message=error_message,
        )

        # Emit job failed event
        failed_result = PrintResult(
            job_id=job_id,
            status="failed",
            error=error_message,
            layout_id=layout_id,
            processed_at=datetime.now(timezone.utc).isoformat(),
        )

        await context.emit(
            {
                "topic": "job.failed",
                "data": {
                    "job_id": job_id,
                    "user_id": user_id,
                    "process_id": "PrintReport",
                    "status": "failed",
                    "error": error_message,
                    "result": failed_result.model_dump(),
                },
            }
        )

        raise
