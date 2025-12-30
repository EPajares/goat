"""
Log analysis results step.

This step logs completed/failed analysis results and can be extended
to store job status in a database, send notifications, etc.
"""

import sys; sys.path.insert(0, "/app/apps/processes/src")  # noqa: E702
import lib.paths  # noqa: F401 - sets up remaining paths

from typing import Optional

from pydantic import BaseModel


class AnalysisLogInput(BaseModel):
    """Input schema for analysis log step."""

    jobId: str
    tool_name: str
    status: str
    output_layer_id: Optional[str] = None
    feature_count: Optional[int] = None
    geometry_type: Optional[str] = None
    error: Optional[str] = None
    processedAt: str


config = {
    "name": "LogAnalysisResult",
    "type": "event",
    "description": "Logs analysis operation results",
    "subscribes": ["analysis-completed", "analysis-failed"],
    "emits": [],
    "flows": ["analysis-flow"],
    "input": AnalysisLogInput.model_json_schema(),
}


async def handler(input_data, context):
    """Log the analysis result."""
    job_id = input_data.get("jobId")
    tool_name = input_data.get("tool_name")
    status = input_data.get("status")
    output_layer_id = input_data.get("output_layer_id")
    feature_count = input_data.get("feature_count")
    error = input_data.get("error")

    if status == "completed":
        context.logger.info(
            f"Analysis {tool_name} completed",
            {
                "job_id": job_id,
                "tool_name": tool_name,
                "output_layer_id": output_layer_id,
                "feature_count": feature_count,
            },
        )
    else:
        context.logger.error(
            f"Analysis {tool_name} failed",
            {
                "job_id": job_id,
                "tool_name": tool_name,
                "error": error,
            },
        )

    # TODO: Could store job status in database here
    # TODO: Could send notifications (email, webhook) here

    return {"logged": True, "job_id": job_id, "status": status}
