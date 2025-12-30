"""
LayerExport Process Step - OGC API Processes

Handles export of layers from DuckLake to various file formats.
Uploads result to S3 and provides presigned download URL.

OGC Process ID: LayerExport
Topics: layer-export-requested -> layer-export-completed / layer-export-failed
"""

import sys; sys.path.insert(0, "/app/apps/processes/src")  # noqa: E702
import lib.paths  # noqa: F401 - sets up remaining paths

import io
import os
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class LayerExportInput(BaseModel):
    """Input schema for LayerExport process."""

    job_id: str = Field(..., description="Job UUID for tracking")
    user_id: str = Field(..., description="User UUID (requester)")
    layer_id: str = Field(..., description="Layer UUID to export")
    layer_owner_id: str = Field(
        ..., description="Layer owner UUID (for DuckLake lookup)"
    )

    # Export options
    file_type: str = Field(
        ..., description="Output format (gpkg, geojson, csv, xlsx, kml, shp)"
    )
    file_name: str = Field(..., description="Output file name (without extension)")
    crs: Optional[str] = Field(None, description="Target CRS for reprojection")
    query: Optional[str] = Field(None, description="WHERE clause filter")


class LayerExportResult(BaseModel):
    """Result schema for LayerExport process."""

    job_id: str
    layer_id: str
    status: str
    s3_key: Optional[str] = None
    download_url: Optional[str] = None
    file_name: Optional[str] = None
    file_size_bytes: Optional[int] = None
    format: Optional[str] = None
    error: Optional[str] = None
    processed_at: str


config = {
    "name": "LayerExport",
    "type": "event",
    "description": "Export a layer from DuckLake to various file formats",
    "subscribes": ["layer-export-requested"],
    "emits": ["job.completed", "job.failed"],
    "flows": ["layer-flow"],
    "input": LayerExportInput.model_json_schema(),
    "infrastructure": {
        "handler": {
            "timeout": 300  # 5 minutes for large exports
        },
        "queue": {
            "visibilityTimeout": 330  # 300 + 30s buffer
        },
    },
}


EXPORT_TIMEOUT_SECONDS = 120


async def handler(input_data: Dict[str, Any], context):
    """Handle layer export request."""
    job_id = input_data.get("job_id")
    user_id = input_data.get("user_id")
    layer_id = input_data.get("layer_id")
    layer_owner_id = input_data.get("layer_owner_id")
    file_type = input_data.get("file_type")
    file_name = input_data.get("file_name")

    context.logger.info(
        "Starting layer export",
        {
            "job_id": job_id,
            "layer_id": layer_id,
            "file_type": file_type,
            "file_name": file_name,
        },
    )

    # Update job status to running in Redis
    from lib.job_state import job_state_manager

    await job_state_manager.update_job_status(
        job_id=job_id,
        status="running",
        message="Exporting layer data...",
    )

    export_dir = None
    zip_path = None

    try:
        import shutil
        import tempfile
        import zipfile

        from lib.config import get_settings
        from lib.layer_service import layer_importer
        from lib.s3 import get_s3_service

        settings = get_settings()
        s3_service = get_s3_service()

        # Create export directory
        export_dir = tempfile.mkdtemp(prefix="goat_export_")
        output_dir = os.path.join(export_dir, file_name)
        os.makedirs(output_dir, exist_ok=True)

        # Build output path
        output_path = os.path.join(output_dir, f"{file_name}.{file_type}")

        context.logger.info(
            "Exporting to format",
            {
                "output_path": output_path,
                "format": file_type.upper(),
                "timeout": EXPORT_TIMEOUT_SECONDS,
            },
        )

        # Export from DuckLake
        # IMPORTANT: Use layer_owner_id for DuckLake lookup (table is in owner's schema)
        layer_importer.export_layer(
            user_id=UUID(layer_owner_id),
            layer_id=UUID(layer_id),
            output_path=output_path,
            output_format=file_type.upper(),
            target_crs=input_data.get("crs"),
            query=input_data.get("query"),
            timeout_seconds=EXPORT_TIMEOUT_SECONDS,
        )

        # Create metadata file
        metadata_path = os.path.join(output_dir, "metadata.txt")
        with open(metadata_path, "w") as f:
            f.write("=" * 60 + "\n")
            f.write(f"Layer Export: {file_name}\n")
            f.write("=" * 60 + "\n")
            f.write(f"Exported: {datetime.now().isoformat()}\n")
            f.write(f"Format: {file_type}\n")
            if input_data.get("crs"):
                f.write(f"CRS: {input_data['crs']}\n")
            f.write("=" * 60 + "\n")

        # Create zip file
        zip_path = os.path.join(export_dir, f"{file_name}.zip")
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(output_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, output_dir)
                    zipf.write(file_path, arcname)

        # Get file size
        file_size = os.path.getsize(zip_path)

        context.logger.info(
            "Export complete, uploading to S3",
            {"zip_path": zip_path, "file_size": file_size},
        )

        # Generate S3 key
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        s3_key = s3_service.build_s3_key(
            settings.S3_BUCKET_PATH or "",
            "exports",
            user_id,
            f"{file_name}_{timestamp}.zip",
        )

        # Upload to S3
        with open(zip_path, "rb") as f:
            file_content = f.read()

        s3_service.upload_file(
            file_content=io.BytesIO(file_content),
            bucket_name=settings.S3_BUCKET_NAME,
            s3_key=s3_key,
            content_type="application/zip",
        )

        # Generate presigned download URL (24 hours)
        download_url = s3_service.generate_presigned_download_url(
            bucket_name=settings.S3_BUCKET_NAME,
            s3_key=s3_key,
            expires_in=86400,  # 24 hours
            filename=f"{file_name}.zip",
        )

        context.logger.info(
            "Upload complete",
            {"s3_key": s3_key},
        )

        # Build success response
        result = LayerExportResult(
            job_id=job_id,
            layer_id=layer_id,
            status="completed",
            s3_key=s3_key,
            download_url=download_url,
            file_name=f"{file_name}.zip",
            file_size_bytes=file_size,
            format=file_type,
            processed_at=datetime.now(timezone.utc).isoformat(),
        )

        # Update Redis job status to successful
        from lib.job_state import job_state_manager

        await job_state_manager.update_job_status(
            job_id=job_id,
            status="successful",
            message="Layer exported successfully",
        )

        # Emit success events
        await context.emit(
            {
                "topic": "layer-export-completed",
                "data": result.model_dump(),
            }
        )

        await context.emit(
            {
                "topic": "job.completed",
                "data": {
                    "job_id": job_id,
                    "user_id": user_id,
                    "status": "successful",
                    "result": {
                        "s3_key": s3_key,
                        "download_url": download_url,
                        "file_name": f"{file_name}.zip",
                        "file_size_bytes": file_size,
                        "format": file_type,
                        "layer_id": layer_id,
                    },
                },
            }
        )

        return result.model_dump()

    except Exception as e:
        error_msg = str(e)
        context.logger.error(
            "Layer export failed",
            {
                "job_id": job_id,
                "error": error_msg,
            },
        )

        # Build error response
        result = LayerExportResult(
            job_id=job_id,
            layer_id=layer_id,
            status="failed",
            error=error_msg,
            processed_at=datetime.now(timezone.utc).isoformat(),
        )

        # Update Redis job status to failed
        from lib.job_state import job_state_manager

        await job_state_manager.update_job_status(
            job_id=job_id,
            status="failed",
            message=error_msg,
        )

        # Emit failure events
        await context.emit(
            {
                "topic": "layer-export-failed",
                "data": result.model_dump(),
            }
        )

        await context.emit(
            {
                "topic": "job.failed",
                "data": {
                    "job_id": job_id,
                    "user_id": user_id,
                    "status": "failed",
                    "error": error_msg,
                },
            }
        )

        return result.model_dump()

    finally:
        # Cleanup temp files
        if export_dir and os.path.exists(export_dir):
            try:
                import shutil

                shutil.rmtree(export_dir)
            except Exception as cleanup_error:
                context.logger.info(
                    "Failed to cleanup export directory: %s", str(cleanup_error)
                )
