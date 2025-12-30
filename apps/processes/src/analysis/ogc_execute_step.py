"""
OGC API Processes - Execute Process
POST /processes/{processId}/execution

Executes a process synchronously or asynchronously based on process capabilities.

For async processes (most vector analysis tools, layer operations):
- Returns 201 Created with job status
- Job processes in background via event emission

For sync processes (statistics tools):
- Returns 200 OK with results directly
- Executes immediately without creating a job
"""

import sys

sys.path.insert(0, "/app/apps/processes/src")  # noqa: E702
from datetime import datetime, timezone
from typing import Any, Dict
from uuid import uuid4

import lib.paths  # noqa: F401 - sets up remaining paths
from lib.auth import auth_middleware
from lib.ogc_base import (
    error_response,
    get_base_url,
    not_found_response,
    pydantic_response,
)
from lib.ogc_process_generator import LAYER_PROCESSES
from lib.ogc_schemas import (
    OGC_EXCEPTION_INVALID_PARAMETER,
    Link,
    StatusCode,
    StatusInfo,
)
from lib.tool_registry import get_tool

# Map layer process IDs to their event topics
LAYER_PROCESS_TOPICS = {
    "LayerImport": "layer-import-requested",
    "LayerExport": "layer-export-requested",
    "LayerUpdate": "layer-update-requested",
    "LayerDelete": "layer-delete-requested",
}

config = {
    "name": "OGCExecuteProcess",
    "type": "api",
    "path": "/processes/:processId/execution",
    "method": "POST",
    "description": "OGC API Processes - execute a process (sync or async based on process capabilities)",
    "emits": [
        "analysis-requested",
        "layer-import-requested",
        "layer-export-requested",
        "layer-update-requested",
        "layer-delete-requested",
    ],
    "flows": ["analysis-flow", "layer-flow"],
    "middleware": [auth_middleware],
}


async def _execute_sync_statistics(
    tool_info, inputs: Dict[str, Any], context
) -> Dict[str, Any]:
    """Execute statistics tool synchronously and return results.

    Args:
        tool_info: Tool information from registry
        inputs: Input parameters
        context: Motia context for logging

    Returns:
        Results from the statistics function
    """
    # Import GOAT Core components (lazy import)
    from core.core.config import settings
    from core.storage.ducklake import ducklake_manager

    # Initialize DuckLake if not already done
    if not ducklake_manager._connection:
        ducklake_manager.init(settings)

    # Get the execute function (stored as tool_class for statistics)
    execute_fn = tool_info.tool_class._fn

    # Get layer information from inputs
    collection = inputs.get("collection")
    user_id = inputs.get("user_id")

    if not collection:
        raise ValueError("'collection' is required for statistics operations")

    # Get table name from DuckLake
    layer_table = ducklake_manager.get_user_layer_table(user_id, collection)
    if not layer_table:
        raise ValueError(f"Collection '{collection}' not found for user")

    # Build where clause from filter (CQL2 filter support can be added later)
    where_clause = "TRUE"
    filter_expr = inputs.get("filter")
    if filter_expr:
        # For now, pass filter as-is (assume SQL-compatible)
        # TODO: Add CQL2 to SQL conversion
        where_clause = filter_expr

    # Get DuckDB connection
    con = ducklake_manager.get_connection()

    # Build function arguments based on tool type
    tool_name = tool_info.name

    if tool_name == "feature_count":
        result = execute_fn(
            con=con,
            table_name=layer_table,
            where_clause=where_clause,
        )
    elif tool_name == "unique_values":
        attribute = inputs.get("attribute")
        if not attribute:
            raise ValueError("'attribute' is required for unique_values")

        from goatlib.analysis.statistics import SortOrder

        order = SortOrder(inputs.get("order", "descendent"))
        limit = inputs.get("limit", 100)
        offset = inputs.get("offset", 0)

        result = execute_fn(
            con=con,
            table_name=layer_table,
            attribute=attribute,
            where_clause=where_clause,
            order=order,
            limit=limit,
            offset=offset,
        )
    elif tool_name == "class_breaks":
        attribute = inputs.get("attribute")
        if not attribute:
            raise ValueError("'attribute' is required for class_breaks")

        from goatlib.analysis.statistics import ClassBreakMethod

        method = ClassBreakMethod(inputs.get("method", "quantile"))
        num_breaks = inputs.get("breaks", 5)
        strip_zeros = inputs.get("strip_zeros", False)

        result = execute_fn(
            con=con,
            table_name=layer_table,
            attribute=attribute,
            method=method,
            num_breaks=num_breaks,
            where_clause=where_clause,
            strip_zeros=strip_zeros,
        )
    elif tool_name == "area_statistics":
        from goatlib.analysis.statistics import AreaOperation

        operation = AreaOperation(inputs.get("operation", "sum"))
        geometry_column = inputs.get("geometry_column", "geom")

        result = execute_fn(
            con=con,
            table_name=layer_table,
            geometry_column=geometry_column,
            operation=operation,
            where_clause=where_clause,
        )
    else:
        raise ValueError(f"Unknown statistics tool: {tool_name}")

    # Return result as dict
    return result.model_dump()


async def handler(req, context):
    """Handle POST /processes/{processId}/execution request."""
    process_id = req.get("pathParams", {}).get("processId")

    if not process_id:
        return error_response(400, "Bad request", "processId is required")

    base_url = get_base_url(req)

    # Get user_id from auth middleware (attached to request)
    user_id = req.get("user_id")
    if not user_id:
        return error_response(401, "Unauthorized", "Authentication required")

    # Get inputs from request body
    body = req.get("body", {})
    inputs = body.get("inputs", body)  # Support both {inputs: {...}} and direct {...}

    # Add user_id to inputs for downstream processing
    inputs["user_id"] = str(user_id)

    context.logger.info(
        "OGC Execute process requested",
        {"process_id": process_id, "base_url": base_url, "user_id": str(user_id)},
    )

    # Check if this is a layer process
    if process_id in LAYER_PROCESSES:
        return await _execute_layer_process(process_id, inputs, base_url, context)

    # Validate process exists in tool registry
    tool_info = get_tool(process_id)
    if not tool_info:
        return not_found_response("process", process_id)

    # user_id is already set from auth middleware
    user_id = inputs.get("user_id")

    # Generate job ID and output layer ID
    job_id = f"{process_id}-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}-{uuid4().hex[:8]}"
    output_layer_id = inputs.get("output_layer_id") or str(uuid4())
    timestamp = datetime.now(timezone.utc).isoformat()

    context.logger.info(
        "Executing process",
        {
            "process_id": process_id,
            "job_id": job_id,
            "user_id": user_id,
            "sync_execute": tool_info.supports_sync,
        },
    )

    # Check if this is a sync-execute process (like statistics)
    if tool_info.supports_sync:
        try:
            context.logger.info(
                f"Executing {process_id} synchronously",
                {"tool_name": process_id},
            )

            result = await _execute_sync_statistics(tool_info, inputs, context)

            context.logger.info(
                f"{process_id} completed successfully",
                {"result_keys": list(result.keys())},
            )

            # Return 200 OK with results directly (OGC sync-execute response)
            return {"status": 200, "body": result}

        except ValueError as e:
            return error_response(
                400, "Invalid parameter", str(e), OGC_EXCEPTION_INVALID_PARAMETER
            )
        except Exception as e:
            context.logger.error(f"Error executing {process_id}", {"error": str(e)})
            return error_response(
                500,
                "Execution failed",
                str(e),
                "http://www.opengis.net/def/exceptions/ogcapi-processes-1/1.0/internal-error",
            )

    # Async execution for traditional vector analysis tools
    event_data = {
        "jobId": job_id,
        "timestamp": timestamp,
        "tool_name": process_id,
        "output_layer_id": output_layer_id,
        **inputs,
    }

    # Store job in Redis for tracking
    from lib.job_state import job_state_manager

    await job_state_manager.create_job(
        job_id=job_id,
        user_id=user_id,
        process_id=process_id,
        status="accepted",
        inputs=inputs,
    )

    # Emit event for background processing
    await context.emit({"topic": "analysis-requested", "data": event_data})

    # Return 201 Created with job status
    status_info = StatusInfo(
        processID=process_id,
        jobID=job_id,
        status=StatusCode.accepted,
        message="Job submitted for processing",
        created=timestamp,
        links=[
            Link(
                href=f"{base_url}/jobs/{job_id}",
                rel="self",
                type="application/json",
                title="Job status",
            ),
            Link(
                href=f"{base_url}/jobs/{job_id}/results",
                rel="http://www.opengis.net/def/rel/ogc/1.0/results",
                type="application/json",
                title="Job results",
            ),
        ],
    )

    return pydantic_response(status_info, status=201)


async def _execute_layer_process(
    process_id: str,
    inputs: Dict[str, Any],
    base_url: str,
    context,
) -> Dict[str, Any]:
    """Execute a layer process (import/export/update).

    All layer processes are async-only.
    user_id is already set in inputs by the handler from auth middleware.
    """
    # user_id is already in inputs from handler
    user_id = inputs.get("user_id")

    # Generate job ID
    job_id = (
        inputs.get("job_id")
        or f"{process_id}-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}-{uuid4().hex[:8]}"
    )
    timestamp = datetime.now(timezone.utc).isoformat()

    context.logger.info(
        "Executing layer process",
        {
            "process_id": process_id,
            "job_id": job_id,
            "user_id": user_id,
        },
    )

    # Validate process-specific required inputs
    if process_id == "LayerImport":
        if not inputs.get("layer_id"):
            return error_response(
                400,
                "Missing input",
                "'layer_id' is required",
                OGC_EXCEPTION_INVALID_PARAMETER,
            )
        if not inputs.get("folder_id"):
            return error_response(
                400,
                "Missing input",
                "'folder_id' is required",
                OGC_EXCEPTION_INVALID_PARAMETER,
            )
        if not inputs.get("name"):
            return error_response(
                400,
                "Missing input",
                "'name' is required",
                OGC_EXCEPTION_INVALID_PARAMETER,
            )
        if not inputs.get("s3_key") and not inputs.get("wfs_url"):
            return error_response(
                400,
                "Missing input",
                "Either 's3_key' or 'wfs_url' is required",
                OGC_EXCEPTION_INVALID_PARAMETER,
            )

    elif process_id == "LayerExport":
        if not inputs.get("layer_id"):
            return error_response(
                400,
                "Missing input",
                "'layer_id' is required",
                OGC_EXCEPTION_INVALID_PARAMETER,
            )
        if not inputs.get("layer_owner_id"):
            return error_response(
                400,
                "Missing input",
                "'layer_owner_id' is required",
                OGC_EXCEPTION_INVALID_PARAMETER,
            )
        if not inputs.get("file_type"):
            return error_response(
                400,
                "Missing input",
                "'file_type' is required",
                OGC_EXCEPTION_INVALID_PARAMETER,
            )
        if not inputs.get("file_name"):
            return error_response(
                400,
                "Missing input",
                "'file_name' is required",
                OGC_EXCEPTION_INVALID_PARAMETER,
            )

    elif process_id == "LayerUpdate":
        if not inputs.get("layer_id"):
            return error_response(
                400,
                "Missing input",
                "'layer_id' is required",
                OGC_EXCEPTION_INVALID_PARAMETER,
            )
        if not inputs.get("s3_key") and not inputs.get("refresh_wfs"):
            return error_response(
                400,
                "Missing input",
                "Either 's3_key' or 'refresh_wfs' is required",
                OGC_EXCEPTION_INVALID_PARAMETER,
            )

    # Build event data
    event_data = {
        "job_id": job_id,
        "timestamp": timestamp,
        **inputs,
    }

    # Store job in Redis for tracking
    from lib.job_state import job_state_manager

    await job_state_manager.create_job(
        job_id=job_id,
        user_id=user_id,
        process_id=process_id,
        status="accepted",
        inputs=inputs,
    )

    # Get the topic for this process
    topic = LAYER_PROCESS_TOPICS.get(process_id)
    if not topic:
        return error_response(
            500, "Configuration error", f"No topic defined for {process_id}"
        )

    # Emit event for background processing
    await context.emit({"topic": topic, "data": event_data})

    # Return 201 Created with job status
    status_info = StatusInfo(
        processID=process_id,
        jobID=job_id,
        status=StatusCode.accepted,
        message="Job submitted for processing",
        created=timestamp,
        links=[
            Link(
                href=f"{base_url}/jobs/{job_id}",
                rel="self",
                type="application/json",
                title="Job status",
            ),
            Link(
                href=f"{base_url}/jobs/{job_id}/results",
                rel="http://www.opengis.net/def/rel/ogc/1.0/results",
                type="application/json",
                title="Job results",
            ),
        ],
    )

    return pydantic_response(status_info, status=201)
