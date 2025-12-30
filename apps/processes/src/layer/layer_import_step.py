"""
LayerImport Process Step - OGC API Processes

Handles import of geospatial data from S3 or WFS into DuckLake storage.
Creates layer metadata in PostgreSQL after successful import.

OGC Process ID: LayerImport
Topics: layer-import-requested -> layer-import-completed / layer-import-failed
"""

import sys; sys.path.insert(0, "/app/apps/processes/src")  # noqa: E702
import lib.paths  # noqa: F401 - sets up remaining paths

from datetime import datetime, timezone
from typing import Any, Dict, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class LayerImportInput(BaseModel):
    """Input schema for LayerImport process."""

    job_id: str = Field(..., description="Job UUID for tracking")
    user_id: str = Field(..., description="User UUID (owner)")
    layer_id: str = Field(..., description="Layer UUID")
    folder_id: str = Field(..., description="Folder UUID to place layer in")

    # Layer metadata
    name: str = Field(..., description="Layer name")
    description: Optional[str] = Field(None, description="Layer description")
    tags: Optional[list[str]] = Field(None, description="Layer tags")

    # Import source (one of these must be provided)
    s3_key: Optional[str] = Field(None, description="S3 key for file import")
    wfs_url: Optional[str] = Field(None, description="WFS service URL")
    wfs_layer_name: Optional[str] = Field(None, description="Specific WFS layer name")

    # WFS metadata (for external service properties)
    data_type: Optional[str] = Field(None, description="Data type (wfs, mvt, etc.)")
    other_properties: Optional[Dict[str, Any]] = Field(
        None, description="External service properties"
    )

    # Optional project link
    project_id: Optional[str] = Field(None, description="Project UUID to link layer to")


class LayerImportResult(BaseModel):
    """Result schema for LayerImport process."""

    job_id: str
    layer_id: str
    status: str
    table_name: Optional[str] = None
    feature_count: Optional[int] = None
    geometry_type: Optional[str] = None
    error: Optional[str] = None
    processed_at: str


config = {
    "name": "LayerImport",
    "type": "event",
    "description": "Import geospatial data from S3 or WFS into DuckLake storage",
    "subscribes": ["layer-import-requested"],
    "emits": ["job.completed", "job.failed"],
    "flows": ["layer-flow"],
    "input": LayerImportInput.model_json_schema(),
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
    """Handle layer import request."""
    job_id = input_data.get("job_id")
    user_id = input_data.get("user_id")
    layer_id = input_data.get("layer_id")

    context.logger.info(
        "Starting layer import",
        {
            "job_id": job_id,
            "user_id": user_id,
            "layer_id": layer_id,
            "s3_key": input_data.get("s3_key"),
            "wfs_url": input_data.get("wfs_url"),
        },
    )

    # Update job status to running in Redis
    from lib.job_state import job_state_manager

    await job_state_manager.update_job_status(
        job_id=job_id,
        status="running",
        message="Importing layer data...",
    )

    try:
        # Import layer service
        from lib.db import get_async_session
        from lib.layer_service import (
            LayerImportResult as ImportResult,
            create_layer_record,
            layer_importer,
        )

        # Determine import source
        s3_key = input_data.get("s3_key")
        wfs_url = input_data.get("wfs_url")

        if not s3_key and not wfs_url:
            raise ValueError("Either s3_key or wfs_url must be provided")

        # Perform import
        if wfs_url:
            context.logger.info("Importing from WFS: %s", wfs_url)
            import_result = layer_importer.import_from_wfs(
                user_id=UUID(user_id),
                layer_id=UUID(layer_id),
                wfs_url=wfs_url,
                layer_name=input_data.get("wfs_layer_name"),
                target_crs="EPSG:4326",
            )
        else:
            context.logger.info("Importing from S3: %s", s3_key)
            import_result = layer_importer.import_from_s3(
                user_id=UUID(user_id),
                layer_id=UUID(layer_id),
                s3_key=s3_key,
                target_crs="EPSG:4326",
            )

        context.logger.info(
            "Import complete, creating layer record",
            {
                "feature_count": import_result.feature_count,
                "geometry_type": import_result.geometry_type,
            },
        )

        # Create layer record in PostgreSQL
        engine, async_session_maker = await get_async_session()
        async with async_session_maker() as session:
            layer = await create_layer_record(
                async_session=session,
                user_id=UUID(user_id),
                layer_id=UUID(layer_id),
                job_id=None,  # Layer processes use string job IDs, not UUIDs
                folder_id=UUID(input_data["folder_id"]),
                name=input_data["name"],
                import_result=import_result,
                description=input_data.get("description"),
                tags=input_data.get("tags"),
                data_type=input_data.get("data_type"),
                other_properties=input_data.get("other_properties"),
                project_id=UUID(input_data["project_id"])
                if input_data.get("project_id")
                else None,
            )

        await engine.dispose()

        # Build success response
        result = LayerImportResult(
            job_id=job_id,
            layer_id=layer_id,
            status="completed",
            table_name=import_result.table_name,
            feature_count=import_result.feature_count,
            geometry_type=import_result.geometry_type,
            processed_at=datetime.now(timezone.utc).isoformat(),
        )

        context.logger.info(
            "Layer import completed successfully",
            {
                "job_id": job_id,
                "layer_id": layer_id,
                "feature_count": import_result.feature_count,
            },
        )

        # Update Redis job status to successful
        from lib.job_state import job_state_manager

        await job_state_manager.update_job_status(
            job_id=job_id,
            status="successful",
            message="Layer imported successfully",
        )

        # Emit success events
        await context.emit(
            {
                "topic": "layer-import-completed",
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
                        "msg": "Layer imported successfully",
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
            "Layer import failed",
            {
                "job_id": job_id,
                "error": error_msg,
            },
        )

        # Try to cleanup DuckLake table if it was created
        try:
            from lib.layer_service import layer_importer

            layer_importer.delete_layer(UUID(user_id), UUID(layer_id))
            context.logger.info("Cleaned up DuckLake table after failed import")
        except Exception as cleanup_error:
            context.logger.info(
                "Failed to cleanup DuckLake table: %s", str(cleanup_error)
            )

        # Build error response
        result = LayerImportResult(
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
                "topic": "layer-import-failed",
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
