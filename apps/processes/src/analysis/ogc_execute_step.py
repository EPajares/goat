"""
OGC API Processes - Execute Process
POST /processes/{processId}/execution

Executes a process synchronously or asynchronously based on process capabilities.

For async processes (most vector analysis tools):
- Returns 201 Created with job status
- Job processes in background via event emission

For sync processes (statistics tools):
- Returns 200 OK with results directly
- Executes immediately without creating a job
"""

import sys
from datetime import datetime, timezone
from typing import Any, Dict
from uuid import uuid4

# Add paths before any lib imports
for path in [
    "/app/apps/processes/src",
    "/app/apps/core/src",
    "/app/packages/python/goatlib/src",
]:
    if path not in sys.path:
        sys.path.insert(0, path)

from lib.ogc_base import (
    error_response,
    get_base_url,
    not_found_response,
    pydantic_response,
)
from lib.ogc_schemas import (
    OGC_EXCEPTION_INVALID_PARAMETER,
    Link,
    StatusCode,
    StatusInfo,
)
from lib.tool_registry import get_tool

config = {
    "name": "OGCExecuteProcess",
    "type": "api",
    "path": "/processes/:processId/execution",
    "method": "POST",
    "description": "OGC API Processes - execute a process (sync or async based on process capabilities)",
    "emits": ["analysis-requested"],
    "flows": ["analysis-flow"],
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

    # Get inputs from request body
    body = req.get("body", {})
    inputs = body.get("inputs", body)  # Support both {inputs: {...}} and direct {...}

    context.logger.info(
        "OGC Execute process requested",
        {"process_id": process_id, "base_url": base_url},
    )

    # Validate process exists
    tool_info = get_tool(process_id)
    if not tool_info:
        return not_found_response("process", process_id)

    # Validate required inputs
    user_id = inputs.get("user_id")
    if not user_id:
        return error_response(
            400,
            "Missing required input",
            "'user_id' is required in inputs",
            OGC_EXCEPTION_INVALID_PARAMETER,
        )

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
