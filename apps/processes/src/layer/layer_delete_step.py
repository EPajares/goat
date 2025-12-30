"""
LayerDelete Process Step - OGC API Processes

Handles deletion of layers from both DuckLake storage and PostgreSQL metadata.
Supports deleting feature layers, table layers, and external layers (raster, WFS, etc.).

OGC Process ID: LayerDelete
Topics: layer-delete-requested -> job.completed / job.failed
"""

import sys; sys.path.insert(0, "/app/apps/processes/src")  # noqa: E702
import lib.paths  # noqa: F401 - sets up remaining paths

from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class LayerDeleteInput(BaseModel):
    """Input schema for LayerDelete process."""

    job_id: str = Field(..., description="Job UUID for tracking")
    user_id: str = Field(..., description="User UUID (owner)")
    layer_id: str = Field(..., description="Layer UUID to delete")


class LayerDeleteResult(BaseModel):
    """Result schema for LayerDelete process."""

    job_id: str
    layer_id: str
    status: str  # "success" or "failed"
    ducklake_deleted: bool = False  # True if DuckLake data was deleted
    metadata_deleted: bool = False  # True if PostgreSQL metadata was deleted
    error: Optional[str] = None
    processed_at: str


config = {
    "name": "LayerDelete",
    "type": "event",
    "description": "Delete a layer from DuckLake storage and PostgreSQL metadata",
    "subscribes": ["layer-delete-requested"],
    "emits": ["job.completed", "job.failed"],
    "flows": ["layer-flow"],
    "input": LayerDeleteInput.model_json_schema(),
    "infrastructure": {
        "handler": {
            "timeout": 60  # 1 minute should be plenty for deletion
        },
        "queue": {
            "visibilityTimeout": 90  # 60 + 30s buffer
        },
    },
}


async def handler(input_data: dict, context) -> LayerDeleteResult:
    """Handle layer deletion.

    Process flow:
    1. Get layer metadata from PostgreSQL using Layer model
    2. Delete data from DuckLake (for feature/table layers)
    3. Delete layer record from PostgreSQL (cascade deletes links)

    Args:
        input_data: LayerDeleteInput as dict
        context: Motia context with logger and emit

    Returns:
        LayerDeleteResult with deletion status
    """
    from sqlalchemy import select

    from lib.db import Layer, get_async_session
    from lib.ducklake import get_ducklake_manager
    from lib.job_state import job_state_manager

    # Parse and validate input
    data = LayerDeleteInput(**input_data)
    job_id = data.job_id  # Keep as string (OGC job ID format)
    user_id = UUID(data.user_id)
    layer_id = UUID(data.layer_id)

    context.logger.info(
        "Starting layer deletion",
        {"job_id": job_id, "layer_id": str(layer_id), "user_id": str(user_id)},
    )

    result = LayerDeleteResult(
        job_id=job_id,
        layer_id=str(layer_id),
        status="failed",  # Default to failed, set to success at end
        processed_at=datetime.now(timezone.utc).isoformat(),
    )

    # Update job status to running
    await job_state_manager.update_job_status(
        job_id=job_id,
        status="running",
        message="Deleting layer...",
    )

    # Get DuckLake manager
    ducklake_manager = get_ducklake_manager()

    engine, async_session_maker = await get_async_session()

    try:
        async with async_session_maker() as session:
            # 1. Get layer using SQLAlchemy model
            stmt = select(Layer).where(Layer.id == layer_id)
            query_result = await session.execute(stmt)
            layer = query_result.scalars().first()

            if not layer:
                raise ValueError(f"Layer not found: {layer_id}")

            # Verify ownership
            if layer.user_id != user_id:
                raise PermissionError(
                    f"User {user_id} does not own layer {layer_id} (owned by {layer.user_id})"
                )

            # Get layer type as string (handle both enum and string cases)
            layer_type = (
                layer.type.value if hasattr(layer.type, "value") else str(layer.type)
            )
            context.logger.info("Found layer", {"name": layer.name, "type": layer_type})

            # 2. Delete DuckLake data for feature/table layers
            if layer_type in ("feature", "table"):
                try:
                    deleted = ducklake_manager.delete_layer_table(
                        user_id=user_id,
                        layer_id=layer_id,
                    )
                    result.ducklake_deleted = deleted
                    if deleted:
                        context.logger.info(
                            "Deleted DuckLake table", {"layer_id": str(layer_id)}
                        )
                    else:
                        context.logger.info(
                            "No DuckLake table found", {"layer_id": str(layer_id)}
                        )
                except Exception as e:
                    context.logger.warn(
                        "Error deleting DuckLake table", {"error": str(e)}
                    )
                    # Continue with metadata deletion even if DuckLake deletion fails

            # 3. Delete layer record (cascade deletes layer_project_link due to FK constraint)
            await session.delete(layer)
            await session.commit()

            result.metadata_deleted = True
            context.logger.info("Deleted layer metadata", {"layer_id": str(layer_id)})

            result.status = "success"

            # Update job status to successful
            await job_state_manager.update_job_status(
                job_id=job_id,
                status="successful",
                message="Layer deleted successfully",
            )

            context.logger.info("Layer deletion completed", {"layer_id": str(layer_id)})

            # Emit success event
            await context.emit(
                {
                    "topic": "job.completed",
                    "data": {
                        "job_id": job_id,
                        "process_id": "LayerDelete",
                        "result": result.model_dump(),
                    },
                }
            )

            return result

    except PermissionError as e:
        error_msg = str(e)
        context.logger.error("Permission denied", {"error": error_msg})

        await job_state_manager.update_job_status(
            job_id=job_id,
            status="failed",
            message=error_msg,
        )

        result.error = error_msg
        await context.emit(
            {
                "topic": "job.failed",
                "data": {
                    "job_id": job_id,
                    "process_id": "LayerDelete",
                    "error": error_msg,
                },
            }
        )
        return result

    except Exception as e:
        error_msg = str(e)
        context.logger.error("Layer deletion failed", {"error": error_msg})

        await job_state_manager.update_job_status(
            job_id=job_id,
            status="failed",
            message=error_msg,
        )

        result.error = error_msg
        await context.emit(
            {
                "topic": "job.failed",
                "data": {
                    "job_id": job_id,
                    "process_id": "LayerDelete",
                    "error": error_msg,
                },
            }
        )
        return result

    finally:
        await engine.dispose()
