"""
List tools API step - returns auto-discovered tools from goatlib.

This Python step provides the actual tool registry data to the API.

Query params:
- include_schema=true: Include JSON schema for each tool's parameters
"""

import sys

sys.path.insert(0, "/app/apps/processes/src")
import lib.paths  # type: ignore # noqa: F401 - sets up sys.path
from lib.tool_registry import get_tool_schema, get_tools_metadata

config = {
    "name": "ListToolsPython",
    "type": "api",
    "path": "/tools",
    "method": "GET",
    "description": "List all available analysis tools (auto-discovered from goatlib)",
    "emits": [],
    "flows": ["analysis-flow"],
}


async def handler(req, context):
    """Return list of auto-discovered tools from goatlib.

    Query params:
        include_schema: If "true", include JSON schema for each tool
        tool: If provided, return only schema for that specific tool
    """
    context.logger.info("Listing available tools from Python registry")

    # In Motia, req is a dict with keys: body, headers, pathParams, queryParams, rawBody
    query_params = req.get("queryParams") or {}

    include_schema = str(query_params.get("include_schema", "")).lower() == "true"
    specific_tool = query_params.get("tool")

    # If requesting a specific tool's schema
    if specific_tool:
        schema = get_tool_schema(specific_tool)
        if schema:
            return {
                "status": 200,
                "body": {"tool": specific_tool, "schema": schema},
            }
        else:
            return {
                "status": 404,
                "body": {"error": f"Tool '{specific_tool}' not found"},
            }

    # Return all tools (with or without schemas)
    tools = get_tools_metadata(include_schema=include_schema)

    return {
        "status": 200,
        "body": {"tools": tools},
    }
