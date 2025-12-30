"""
LayerUpdate Process Step - OGC API Processes

Handles updating existing layer data from S3 or WFS (refresh).
Deletes old DuckLake data and imports fresh data.

OGC Process ID: LayerUpdate
Topics: layer-update-requested -> layer-update-completed / layer-update-failed
"""

import sys; sys.path.insert(0, "/app/apps/processes/src")  # noqa: E702
import lib.paths  # noqa: F401 - sets up remaining paths

from datetime import datetime, timezone
from typing import Any, Dict, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class LayerUpdateInput(BaseModel):
    """Input schema for LayerUpdate process."""

    job_id: str = Field(..., description="Job UUID for tracking")
    user_id: str = Field(..., description="User UUID (owner)")
    layer_id: str = Field(..., description="Layer UUID to update")

    # Update source (one of these must be provided)
    s3_key: Optional[str] = Field(None, description="S3 key for file import")
    refresh_wfs: bool = Field(False, description="Whether to refresh from WFS source")

    # WFS metadata (for refresh)
    wfs_url: Optional[str] = Field(None, description="Original WFS URL")
    wfs_layer_name: Optional[str] = Field(None, description="WFS layer name")


class LayerUpdateResult(BaseModel):
    """Result schema for LayerUpdate process."""

    job_id: str
    layer_id: str
    status: str
    table_name: Optional[str] = None
    feature_count: Optional[int] = None
    geometry_type: Optional[str] = None
    error: Optional[str] = None
    processed_at: str


config = {
    "name": "LayerUpdate",
    "type": "event",
    "description": "Update existing layer data from S3 or WFS (refresh)",
    "subscribes": ["layer-update-requested"],
    "emits": ["job.completed", "job.failed"],
    "flows": ["layer-flow"],
    "input": LayerUpdateInput.model_json_schema(),
    "infrastructure": {
        "handler": {
            "timeout": 300  # 5 minutes for large files
        },
        "queue": {
            "visibilityTimeout": 330  # 300 + 30s buffer
        },
    },
}


async def handler(input_data: Dict[str, Any], context):
    """Handle layer update request."""
    job_id = input_data.get("job_id")
    user_id = input_data.get("user_id")
    layer_id = input_data.get("layer_id")

    context.logger.info(
        "Starting layer update",
        {
            "job_id": job_id,
            "user_id": user_id,
            "layer_id": layer_id,
            "s3_key": input_data.get("s3_key"),
            "refresh_wfs": input_data.get("refresh_wfs"),
        },
    )

    # Update job status to running in Redis
    from lib.job_state import job_state_manager

    await job_state_manager.update_job_status(
        job_id=job_id,
        status="running",
        message="Updating layer data...",
    )

    try:
        from lib.layer_service import layer_importer

        # Determine update source
        s3_key = input_data.get("s3_key")
        refresh_wfs = input_data.get("refresh_wfs", False)
        wfs_url = input_data.get("wfs_url")
        wfs_layer_name = input_data.get("wfs_layer_name")

        if not s3_key and not refresh_wfs:
            raise ValueError("Either s3_key or refresh_wfs must be provided")

        if refresh_wfs and not wfs_url:
            raise ValueError("wfs_url is required for WFS refresh")

        # Use unified update method
        import_result = layer_importer.update_layer_dataset(
            user_id=UUID(user_id),
            layer_id=UUID(layer_id),
            s3_key=s3_key if not refresh_wfs else None,
            wfs_url=wfs_url if refresh_wfs else None,
            wfs_layer_name=wfs_layer_name,
            target_crs="EPSG:4326",
        )

        context.logger.info(
            "Layer update complete",
            {
                "feature_count": import_result.feature_count,
                "geometry_type": import_result.geometry_type,
            },
        )

        # Build success response
        result = LayerUpdateResult(
            job_id=job_id,
            layer_id=layer_id,
            status="completed",
            table_name=import_result.table_name,
            feature_count=import_result.feature_count,
            geometry_type=import_result.geometry_type,
            processed_at=datetime.now(timezone.utc).isoformat(),
        )

        # Update Redis job status to successful
        from lib.job_state import job_state_manager

        await job_state_manager.update_job_status(
            job_id=job_id,
            status="successful",
            message="Layer updated successfully",
        )

        # Emit success events
        await context.emit(
            {
                "topic": "layer-update-completed",
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
                        "msg": "Layer updated successfully",
                        "layer_id": layer_id,
                        "table_name": import_result.table_name,
                        "feature_count": import_result.feature_count,
                        "geometry_type": import_result.geometry_type,
                    },
                },
            }
        )

        return result.model_dump()

    except Exception as e:
        error_msg = str(e)
        context.logger.error(
            "Layer update failed",
            {
                "job_id": job_id,
                "error": error_msg,
            },
        )

        # Build error response
        result = LayerUpdateResult(
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
                "topic": "layer-update-failed",
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
