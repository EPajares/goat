"""
Job schemas for Motia analysis service.

These are Pydantic schemas only - database models are in GOAT Core.
JobType is dynamically derived from registered tools.
Job status uses OGC API Processes StatusCode directly (no mapping needed).

NOTE: Database operations use GOAT Core's Job model (core.db.models.job.Job).
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

# Re-export OGC StatusCode as the canonical job status
from lib.ogc_schemas import StatusCode as JobStatusCode
from pydantic import BaseModel


def get_job_types() -> List[str]:
    """Get list of valid job types from tool registry.

    Each registered tool becomes a valid job type.

    Returns:
        List of tool names that can be used as job types.
        Returns empty list if tool_registry is not available.
    """
    try:
        from lib.tool_registry import get_tool_names

        return get_tool_names()
    except ImportError:
        # No fallback - if tools aren't available, processes won't work
        return []


# === Pydantic Schemas (for API validation) ===


class JobPayload(BaseModel):
    """Standard payload structure for analysis jobs.

    This provides a consistent structure for the JSONB payload field
    stored in GOAT Core's job table.
    """

    # Context
    project_id: Optional[str] = None
    scenario_id: Optional[str] = None

    # Result info (on success)
    result_layer_id: Optional[str] = None
    feature_count: Optional[int] = None
    geometry_type: Optional[str] = None

    # Error info (on failure)
    error_message: Optional[str] = None
    error_type: Optional[str] = None

    # Input tracking
    input_params: Optional[Dict[str, Any]] = None

    # Presigned URL (when save_results=False)
    download_url: Optional[str] = None
    download_expires_at: Optional[datetime] = None


class JobResponse(BaseModel):
    """API response schema for job status.

    Maps GOAT Core Job model to OGC-compatible response.
    """

    id: UUID
    user_id: UUID
    type: str  # Tool name (e.g., "clip", "buffer")
    status: JobStatusCode  # OGC StatusCode
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    payload: Optional[JobPayload] = None

    class Config:
        from_attributes = True  # Allow creating from ORM models
