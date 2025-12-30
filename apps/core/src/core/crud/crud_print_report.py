"""Print Report CRUD operations using Playwright for PDF generation."""

import io
import logging
import re
import zipfile
from datetime import datetime
from typing import Any, Dict, List
from uuid import UUID

from fastapi import BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession

from core.core.config import settings
from core.core.job import (
    CRUDFailedJob,
    job_init,
    job_log,
    run_background_or_immediately,
)
from core.crud.crud_job import job as crud_job
from core.crud.crud_report_layout import report_layout as crud_report_layout
from core.schemas.job import JobStatusType
from core.schemas.print import PrintFormat, PrintReportRequest
from core.services.s3 import s3_service

logger = logging.getLogger(__name__)

# Batch size for atlas page processing - renders this many pages in parallel
ATLAS_BATCH_SIZE = 5  # Keep lower to avoid memory issues with parallel rendering

# Timeout for first page (needs to load all assets)
FIRST_PAGE_TIMEOUT_MS = 60000  # 60 seconds
# Timeout for subsequent pages (assets are cached)
SUBSEQUENT_PAGE_TIMEOUT_MS = 30000  # 30 seconds


def sanitize_filename(name: str) -> str:
    """
    Sanitize a string to be used as a filename.
    Replaces spaces with underscores and removes/replaces special characters.
    """
    # Replace spaces with underscores
    name = name.replace(" ", "_")
    # Remove or replace special characters (keep alphanumeric, underscore, hyphen)
    name = re.sub(r"[^\w\-]", "", name)
    # Remove consecutive underscores
    name = re.sub(r"_+", "_", name)
    # Trim underscores from ends
    name = name.strip("_")
    return name


class CRUDPrintReport(CRUDFailedJob):
    """CRUD operations for print report job."""

    def __init__(
        self,
        job_id: UUID,
        background_tasks: BackgroundTasks,
        async_session: AsyncSession,
        user_id: UUID,
        project_id: UUID,
        access_token: str | None = None,
    ) -> None:
        super().__init__(job_id, background_tasks, async_session, user_id)
        self.project_id = project_id
        self.access_token = access_token

    @run_background_or_immediately(settings)
    @job_init()
    async def run(self, params: PrintReportRequest) -> Dict[str, Any]:
        """Main entry point for the print job."""
        result = await self.generate_print(params=params)
        return result

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

    async def _inject_auth_token(self, page, base_url: str):
        """Navigate to base URL and inject auth token into localStorage."""
        await page.goto(
            f"{base_url}/print", wait_until="domcontentloaded", timeout=10000
        )
        if self.access_token:
            await page.evaluate(
                f'localStorage.setItem("print_access_token", "{self.access_token}")'
            )

    async def _render_page(
        self,
        page,
        print_url: str,
        atlas_page_index: int | None = None,
        is_first_page: bool = True,
    ) -> tuple[str, str, int]:
        """
        Render a single page and return (width_mm, height_mm, total_atlas_pages).

        If atlas_page_index is provided, appends ?page=N to the URL.
        is_first_page uses longer timeouts since assets need to load.
        """
        url = print_url
        if atlas_page_index is not None:
            url = f"{print_url}?page={atlas_page_index}"

        # Use shorter timeout for subsequent pages (assets are cached)
        timeout_ms = (
            FIRST_PAGE_TIMEOUT_MS if is_first_page else SUBSEQUENT_PAGE_TIMEOUT_MS
        )

        await page.goto(
            url,
            wait_until="networkidle",
            timeout=timeout_ms,
        )

        # Wait for the page to signal it's ready
        await page.wait_for_selector(
            '[data-print-ready="true"]',
            state="attached",
            timeout=timeout_ms,
        )

        # Wait for network to be idle (map tiles loading) - shorter for subsequent pages
        network_timeout = 30000 if is_first_page else 15000
        await page.wait_for_load_state("networkidle", timeout=network_timeout)

        # Get metadata
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
        # Target the paper element specifically, not the full page
        paper_element = await page.query_selector("#print-paper")
        if paper_element:
            return await paper_element.screenshot(type="png")
        else:
            # Fallback to full page if paper element not found
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

    def _create_zip(self, images: List[tuple[str, bytes]]) -> bytes:
        """Create a ZIP file from a list of (filename, bytes) tuples."""
        output = io.BytesIO()
        with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as zf:
            for filename, data in images:
                zf.writestr(filename, data)
        return output.getvalue()

    @job_log(job_step_name="print_report")
    async def generate_print(self, params: PrintReportRequest) -> Dict[str, Any]:
        """Generate PDF/PNG using Playwright, with atlas support."""
        try:
            from playwright.async_api import async_playwright
        except ImportError:
            raise ImportError(
                "Playwright is not installed. "
                "Run: pip install playwright && playwright install chromium"
            )

        # Fetch the layout to get its name for the filename
        layout = await crud_report_layout.get_by_project_and_id(
            async_session=self.async_session,
            project_id=self.project_id,
            layout_id=params.layout_id,
        )
        layout_name = layout.name if layout else "Report"

        # Build the base print page URL
        print_url = (
            f"{settings.PRINT_FRONTEND_URL}/print/{self.project_id}/{params.layout_id}"
        )
        logger.info(f"Generating print from URL: {print_url}")

        async with async_playwright() as p:
            browser, context = await self._setup_browser_context(p)

            try:
                page = await context.new_page()
                base_url = settings.PRINT_FRONTEND_URL.rstrip("/")

                # Inject auth token
                await self._inject_auth_token(page, base_url)

                # First, render page 0 to get atlas info
                width_mm, height_mm, atlas_total_pages = await self._render_page(
                    page, print_url, atlas_page_index=0
                )

                # Determine which pages to render
                if atlas_total_pages > 1:
                    # Atlas mode - determine page indices
                    if params.atlas_page_indices:
                        # Specific pages requested
                        page_indices = [
                            i
                            for i in params.atlas_page_indices
                            if 0 <= i < atlas_total_pages
                        ]
                    else:
                        # All pages
                        page_indices = list(range(atlas_total_pages))

                    logger.info(
                        f"Atlas mode: {len(page_indices)} pages to render "
                        f"(total: {atlas_total_pages})"
                    )

                    # Render pages in batches
                    if params.format == PrintFormat.pdf:
                        output_buffer = await self._render_atlas_pdf(
                            page, print_url, page_indices, width_mm, height_mm
                        )
                        page_count = len(page_indices)
                        file_extension = "pdf"
                        content_type = "application/pdf"
                    else:
                        # PNG - create ZIP of images
                        output_buffer = await self._render_atlas_png_zip(
                            page, print_url, page_indices, layout_name
                        )
                        page_count = len(page_indices)
                        file_extension = "zip"
                        content_type = "application/zip"
                else:
                    # Single page mode (no atlas or atlas with 1 page)
                    logger.info("Single page mode")
                    page_count = 1

                    if params.format == PrintFormat.pdf:
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
        s3_key = s3_service.build_s3_key(
            settings.S3_BUCKET_PATH or "",
            settings.PRINT_OUTPUT_DIR or "prints",
            str(self.user_id),
            f"{self.project_id}_{params.layout_id}_{timestamp}.{file_extension}",
        )

        # Upload to S3
        s3_service.upload_file(
            file_content=io.BytesIO(output_buffer),
            bucket_name=settings.S3_BUCKET_NAME or "goat",
            s3_key=s3_key,
            content_type=content_type,
        )

        result_payload = {
            "s3_key": s3_key,
            "file_name": file_name,
            "file_size_bytes": len(output_buffer),
            "page_count": page_count,
            "format": params.format.value,
            "layout_id": str(params.layout_id),
            "layout_name": layout_name,
        }

        logger.info(
            f"Print job completed. S3 key: {s3_key}, file_name: {file_name}, "
            f"pages: {page_count}"
        )

        return {"status": JobStatusType.successful.value, "result": result_payload}

    async def _render_atlas_pdf(
        self,
        page,
        print_url: str,
        page_indices: List[int],
        width_mm: str,
        height_mm: str,
    ) -> bytes:
        """Render atlas pages as PDF in parallel batches and merge them."""
        import asyncio

        all_pdfs: List[bytes] = []
        context = page.context  # Get the browser context to create new pages

        async def render_single_page(idx: int) -> tuple[int, bytes]:
            """Render a single page and return (index, pdf_bytes)."""
            new_page = await context.new_page()
            try:
                url = f"{print_url}?page={idx}"
                await new_page.goto(
                    url,
                    wait_until="networkidle",
                    timeout=SUBSEQUENT_PAGE_TIMEOUT_MS,
                )
                await new_page.wait_for_selector(
                    '[data-print-ready="true"]',
                    state="attached",
                    timeout=SUBSEQUENT_PAGE_TIMEOUT_MS,
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

        # Process in parallel batches
        for batch_start in range(0, len(page_indices), ATLAS_BATCH_SIZE):
            batch_end = min(batch_start + ATLAS_BATCH_SIZE, len(page_indices))
            batch_indices = page_indices[batch_start:batch_end]

            logger.info(
                f"Processing PDF batch {batch_start // ATLAS_BATCH_SIZE + 1}: "
                f"pages {batch_indices[0]+1} to {batch_indices[-1]+1} (parallel)"
            )

            # Run batch in parallel
            tasks = [render_single_page(idx) for idx in batch_indices]
            results = await asyncio.gather(*tasks)

            # Sort by index to maintain page order
            results.sort(key=lambda x: x[0])
            for _, pdf_bytes in results:
                all_pdfs.append(pdf_bytes)

        # Merge all PDFs
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
        import asyncio

        images: List[tuple[str, bytes]] = []
        sanitized_name = sanitize_filename(layout_name)
        context = page.context  # Get the browser context to create new pages

        async def render_single_page(idx: int) -> tuple[int, str, bytes]:
            """Render a single page and return (index, filename, png_bytes)."""
            new_page = await context.new_page()
            try:
                url = f"{print_url}?page={idx}"
                await new_page.goto(
                    url,
                    wait_until="networkidle",
                    timeout=SUBSEQUENT_PAGE_TIMEOUT_MS,
                )
                await new_page.wait_for_selector(
                    '[data-print-ready="true"]',
                    state="attached",
                    timeout=SUBSEQUENT_PAGE_TIMEOUT_MS,
                )
                await new_page.wait_for_load_state("networkidle", timeout=15000)

                png_bytes = await new_page.screenshot(type="png", full_page=True)
                filename = f"{sanitized_name}_{idx + 1:03d}.png"
                return (idx, filename, png_bytes)
            finally:
                await new_page.close()

        # Process in parallel batches
        for batch_start in range(0, len(page_indices), ATLAS_BATCH_SIZE):
            batch_end = min(batch_start + ATLAS_BATCH_SIZE, len(page_indices))
            batch_indices = page_indices[batch_start:batch_end]

            logger.info(
                f"Processing PNG batch {batch_start // ATLAS_BATCH_SIZE + 1}: "
                f"pages {batch_indices[0]+1} to {batch_indices[-1]+1} (parallel)"
            )

            # Run batch in parallel
            tasks = [render_single_page(idx) for idx in batch_indices]
            results = await asyncio.gather(*tasks)

            # Sort by index to maintain page order
            results.sort(key=lambda x: x[0])
            for _, filename, png_bytes in results:
                images.append((filename, png_bytes))

        return self._create_zip(images)


async def start_print_job(
    async_session: AsyncSession,
    user_id: UUID,
    background_tasks: BackgroundTasks,
    project_id: UUID,
    params: PrintReportRequest,
    access_token: str | None = None,
) -> Dict[str, Any]:
    """Start a print report job."""
    from core.schemas.job import JobType

    # Initial payload with layout_id so we can filter by layout in history
    initial_payload = {
        "layout_id": str(params.layout_id),
        "format": params.format.value,
    }

    # Create job with initial payload
    job = await crud_job.check_and_create(
        async_session=async_session,
        user_id=user_id,
        job_type=JobType.print_report,
        project_id=project_id,
        payload=initial_payload,
    )

    # Instantiate the CRUD class
    print_crud = CRUDPrintReport(
        job_id=job.id,
        background_tasks=background_tasks,
        async_session=async_session,
        user_id=user_id,
        project_id=project_id,
        access_token=access_token,
    )

    # Run the job (decorator handles background execution)
    await print_crud.run(params=params)

    return {"job_id": job.id}
