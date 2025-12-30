"""
Generic analysis processor step for ALL goatlib tools.

This step handles any auto-discovered goatlib analysis tool by:
1. Looking up the tool by name from the auto-discovery registry
2. Creating the appropriate LayerParams from input data (dynamically generated)
3. Running the original Tool wrapped with GenericLayerTool for DuckLake support
4. Emitting success or failure events

No tool-specific code is needed - just add *Params/*Tool pairs to goatlib
following the naming convention and:
- LayerParams will be auto-generated
- The tool will be wrapped with GenericLayerTool for DuckLake layer I/O

The registry automatically:
- Discovers all *Params classes from goatlib.analysis.schemas.vector
- Finds matching *Tool classes from goatlib.analysis.vector
- Dynamically generates *LayerParams versions that use layer IDs instead of file paths
"""

import sys
from datetime import datetime, timezone
from typing import Any, Dict, Optional

# Add paths before any lib imports
for path in ["/app/apps/processes/src", "/app/apps/core/src", "/app/packages/python/goatlib/src"]:
    if path not in sys.path:
        sys.path.insert(0, path)
import lib.paths  # type: ignore # noqa: F401 - sets up sys.path
from lib.ogc_exception_handler import format_ogc_error_response
from lib.tool_registry import get_combined_input_schema, get_tool, get_tool_names
from pydantic import BaseModel


class AnalysisResult(BaseModel):
    """Result schema for any analysis operation."""

    jobId: str
    tool_name: str
    status: str
    output_layer_id: Optional[str] = None
    feature_count: Optional[int] = None
    geometry_type: Optional[str] = None
    error: Optional[str] = None
    ogc_error: Optional[Dict[str, Any]] = None  # OGC formatted error
    processedAt: str


config = {
    "name": "ProcessAnalysis",
    "type": "event",
    "description": "Processes any goatlib analysis tool on DuckLake layers (auto-discovered)",
    "subscribes": ["analysis-requested"],
    "emits": ["analysis-completed", "analysis-failed", "job.completed", "job.failed"],
    "flows": ["analysis-flow"],
    "input": get_combined_input_schema(),
    "infrastructure": {
        "handler": {
            "timeout": 120  # 120 seconds max execution time
        },
        "queue": {
            "visibilityTimeout": 150  # 120 + 30s buffer
        },
    },
}


def _build_params(tool_info, input_data: Dict[str, Any]) -> Any:
    """Build tool-specific LayerParams from input data.

    This dynamically creates the params object based on the tool's layer_params_class
    (which is dynamically generated from the original params_class).
    Only includes fields that are defined in the params schema.
    """
    params_class = tool_info.layer_params_class
    schema = params_class.model_json_schema()
    valid_fields = schema.get("properties", {}).keys()

    # Filter input data to only include valid fields for this tool
    params_data = {
        k: v for k, v in input_data.items() if k in valid_fields and v is not None
    }

    return params_class(**params_data)


async def handler(input_data: Dict[str, Any], context):
    """Handle any analysis request using the auto-discovery registry."""
    job_id = input_data.get("jobId")
    tool_name = input_data.get("tool_name")
    user_id = input_data.get("user_id")

    context.logger.info(
        "Starting analysis operation",
        {
            "job_id": job_id,
            "tool_name": tool_name,
            "user_id": user_id,
        },
    )

    # Update job status to running in Redis
    from lib.job_state import job_state_manager

    await job_state_manager.update_job_status(
        job_id=job_id,
        status="running",
        message="Processing analysis...",
    )

    try:
        # Look up tool in registry (auto-discovered)
        tool_info = get_tool(tool_name)
        if not tool_info:
            available = get_tool_names()
            raise ValueError(
                f"Unknown tool: '{tool_name}'. Available tools: {', '.join(available) or 'none'}"
            )

        # Import GOAT Core components (lazy import to avoid startup issues)
        from core.core.config import settings
        from core.storage.ducklake import ducklake_manager

        # Initialize DuckLake if not already done
        if not ducklake_manager._connection:
            ducklake_manager.init(settings)

        # Build params for this specific tool
        params = _build_params(tool_info, input_data)

        context.logger.info(
            f"Running {tool_name} with params",
            {"params": str(params)},
        )

        # Import the generic layer tool wrapper (local lib, not goatlib)
        from lib.layer_tool_wrapper import GenericLayerTool

        # Create wrapped tool that handles DuckLake layer I/O
        wrapped_tool = GenericLayerTool(
            tool_class=tool_info.tool_class,
            params_class=tool_info.params_class,  # Original path-based params
            ducklake_manager=ducklake_manager,
        )

        # Run the tool
        result = wrapped_tool.run(params)

        # Build success response
        analysis_result = AnalysisResult(
            jobId=job_id,
            tool_name=tool_name,
            status="completed",
            output_layer_id=result.output_layer_id,
            feature_count=result.feature_count,
            geometry_type=result.geometry_type,
            processedAt=datetime.now(timezone.utc).isoformat(),
        )

        context.logger.info(
            f"{tool_name} completed successfully",
            {
                "job_id": job_id,
                "output_layer_id": analysis_result.output_layer_id,
                "feature_count": analysis_result.feature_count,
                "download_url": result.download_url is not None,
            },
        )

        await context.emit(
            {
                "topic": "analysis-completed",
                "data": analysis_result.model_dump(),
            }
        )

        # Emit job.completed event for job status persistence
        job_data = {
            "job_id": job_id,
            "user_id": user_id,
            "tool_name": tool_name,
            "status": "successful",  # OGC StatusCode
            "project_id": input_data.get("project_id"),
            "scenario_id": input_data.get("scenario_id"),
            "result_layer_id": analysis_result.output_layer_id,
            "feature_count": analysis_result.feature_count,
            "input_params": {
                k: v for k, v in input_data.items() if k not in ("jobId", "timestamp")
            },
        }

        # Add presigned URL info if save_results=False
        if result.download_url:
            job_data["download_url"] = result.download_url
            job_data["download_expires_at"] = (
                result.download_expires_at.isoformat()
                if result.download_expires_at
                else None
            )

        await context.emit(
            {
                "topic": "job.completed",
                "data": job_data,
            }
        )

        return analysis_result.model_dump()

    except Exception as e:
        context.logger.error(f"{tool_name} failed", {"error": str(e)})

        # Format error as OGC exception
        ogc_error = format_ogc_error_response(e)

        error_result = AnalysisResult(
            jobId=job_id,
            tool_name=tool_name or "unknown",
            status="failed",
            error=str(e),
            ogc_error=ogc_error,
            processedAt=datetime.now(timezone.utc).isoformat(),
        )

        await context.emit(
            {
                "topic": "analysis-failed",
                "data": error_result.model_dump(),
            }
        )

        # Emit job.failed event for job status persistence
        await context.emit(
            {
                "topic": "job.failed",
                "data": {
                    "job_id": job_id,
                    "user_id": user_id,
                    "tool_name": tool_name or "unknown",
                    "status": "failed",  # OGC StatusCode
                    "project_id": input_data.get("project_id"),
                    "scenario_id": input_data.get("scenario_id"),
                    "error_message": str(e),
                    "ogc_error": ogc_error,
                    "input_params": {
                        k: v
                        for k, v in input_data.items()
                        if k not in ("jobId", "timestamp")
                    },
                },
            }
        )

        return error_result.model_dump()
