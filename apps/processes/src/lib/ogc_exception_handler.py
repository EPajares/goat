"""
OGC Exception Handler.

Provides utilities for converting goatlib and other exceptions to OGC-compliant
error responses.

Usage in step handlers:
    from lib.ogc_exception_handler import ogc_exception_handler, OGCError

    async def handler(input_data, context):
        with ogc_exception_handler(context):
            # Your code here - exceptions will be converted to OGC format
            ...

Or raise specific OGC errors:
    raise OGCError.invalid_parameter("input_layer_id", "Layer not found")
    raise OGCError.no_such_process("unknown_tool")
    raise OGCError.no_such_job("job-uuid")
"""

import logging
import re
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Any, Dict, Optional, Tuple

logger = logging.getLogger(__name__)


# OGC Exception type URIs
OGC_EXCEPTION_BASE = "http://www.opengis.net/def/exceptions/ogcapi-processes-1/1.0"

EXCEPTION_TYPES = {
    "InvalidParameterValue": f"{OGC_EXCEPTION_BASE}/InvalidParameterValue",
    "NoSuchProcess": f"{OGC_EXCEPTION_BASE}/NoSuchProcess",
    "NoSuchJob": f"{OGC_EXCEPTION_BASE}/NoSuchJob",
    "ResultNotReady": f"{OGC_EXCEPTION_BASE}/ResultNotReady",
    "JobNotDismissible": f"{OGC_EXCEPTION_BASE}/JobNotDismissible",
    "ServerError": f"{OGC_EXCEPTION_BASE}/ServerError",
}


@dataclass
class OGCException:
    """OGC-compliant exception structure."""

    type: str
    title: str
    status: int
    detail: str
    instance: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON response."""
        result = {
            "type": self.type,
            "title": self.title,
            "status": self.status,
            "detail": self.detail,
        }
        if self.instance:
            result["instance"] = self.instance
        return result


class OGCError(Exception):
    """Raise OGC-compliant errors from handlers."""

    def __init__(self, exception: OGCException) -> None:
        self.exception = exception
        super().__init__(exception.detail)

    @classmethod
    def invalid_parameter(cls, param_name: str, detail: str) -> "OGCError":
        """Invalid parameter value error."""
        return cls(
            OGCException(
                type=EXCEPTION_TYPES["InvalidParameterValue"],
                title=f"Invalid parameter: {param_name}",
                status=400,
                detail=detail,
            )
        )

    @classmethod
    def no_such_process(cls, process_id: str) -> "OGCError":
        """Process not found error."""
        return cls(
            OGCException(
                type=EXCEPTION_TYPES["NoSuchProcess"],
                title="Process not found",
                status=404,
                detail=f"Process '{process_id}' does not exist",
            )
        )

    @classmethod
    def no_such_job(cls, job_id: str) -> "OGCError":
        """Job not found error."""
        return cls(
            OGCException(
                type=EXCEPTION_TYPES["NoSuchJob"],
                title="Job not found",
                status=404,
                detail=f"Job with ID '{job_id}' not found",
            )
        )

    @classmethod
    def result_not_ready(cls, job_id: str, status: str) -> "OGCError":
        """Result not ready error."""
        return cls(
            OGCException(
                type=EXCEPTION_TYPES["ResultNotReady"],
                title="Results not ready",
                status=404,
                detail=f"Job '{job_id}' has status '{status}' - results not available",
            )
        )

    @classmethod
    def server_error(cls, detail: str) -> "OGCError":
        """Internal server error."""
        return cls(
            OGCException(
                type=EXCEPTION_TYPES["ServerError"],
                title="Internal server error",
                status=500,
                detail=detail,
            )
        )


def parse_goatlib_error(error: Exception) -> Tuple[str, str, int]:
    """Parse goatlib error messages into OGC format.

    Returns:
        Tuple of (exception_type, title, status_code)
    """
    error_str = str(error)

    # Geometry type validation errors
    # e.g., "Input layer has geometry type LINESTRING. Accepted types: POLYGON, MULTIPOLYGON"
    geometry_pattern = r"(?:has geometry type|geometry type.*is) (\w+).*(?:Accepted|Expected|allowed).*types?:?\s*([^.]+)"
    match = re.search(geometry_pattern, error_str, re.IGNORECASE)
    if match:
        return (
            EXCEPTION_TYPES["InvalidParameterValue"],
            "Invalid geometry type",
            400,
        )

    # Missing required parameter
    if "required" in error_str.lower() and (
        "missing" in error_str.lower() or "field" in error_str.lower()
    ):
        return (
            EXCEPTION_TYPES["InvalidParameterValue"],
            "Missing required parameter",
            400,
        )

    # Invalid UUID format
    if "uuid" in error_str.lower() or "invalid.*id" in error_str.lower():
        return (
            EXCEPTION_TYPES["InvalidParameterValue"],
            "Invalid identifier format",
            400,
        )

    # Layer not found
    if "layer" in error_str.lower() and (
        "not found" in error_str.lower() or "does not exist" in error_str.lower()
    ):
        return (
            EXCEPTION_TYPES["InvalidParameterValue"],
            "Layer not found",
            404,
        )

    # Unknown tool
    if "unknown tool" in error_str.lower() or "no such process" in error_str.lower():
        return (
            EXCEPTION_TYPES["NoSuchProcess"],
            "Process not found",
            404,
        )

    # Default: treat as server error
    return (
        EXCEPTION_TYPES["ServerError"],
        "Processing error",
        500,
    )


def convert_exception_to_ogc(error: Exception) -> OGCException:
    """Convert any exception to OGC-compliant exception.

    Handles:
    - OGCError: Already formatted, return as-is
    - ValueError from goatlib: Parse and format
    - Other exceptions: Generic server error
    """
    # Already an OGC error
    if isinstance(error, OGCError):
        return error.exception

    # Parse error message
    error_str = str(error)

    # ValueError often comes from goatlib validation
    if isinstance(error, ValueError):
        exc_type, title, status = parse_goatlib_error(error)
        return OGCException(
            type=exc_type,
            title=title,
            status=status,
            detail=error_str,
        )

    # KeyError usually means missing field
    if isinstance(error, KeyError):
        return OGCException(
            type=EXCEPTION_TYPES["InvalidParameterValue"],
            title="Missing required field",
            status=400,
            detail=f"Missing field: {error_str}",
        )

    # TypeError usually means wrong type
    if isinstance(error, TypeError):
        return OGCException(
            type=EXCEPTION_TYPES["InvalidParameterValue"],
            title="Invalid parameter type",
            status=400,
            detail=error_str,
        )

    # RuntimeError from tool execution
    if isinstance(error, RuntimeError):
        return OGCException(
            type=EXCEPTION_TYPES["ServerError"],
            title="Processing failed",
            status=500,
            detail=error_str,
        )

    # Default: server error
    return OGCException(
        type=EXCEPTION_TYPES["ServerError"],
        title="Internal server error",
        status=500,
        detail=error_str,
    )


@contextmanager
def ogc_exception_handler(context):
    """Context manager that catches exceptions and converts to OGC format.

    Usage:
        with ogc_exception_handler(context):
            # Your code here
            ...

    Exceptions will be logged and converted to OGC exception format.
    The converted exception is stored in context._ogc_exception.
    """
    try:
        yield
    except Exception as e:
        ogc_exc = convert_exception_to_ogc(e)
        context.logger.error(
            f"OGC Exception: {ogc_exc.title}",
            {
                "type": ogc_exc.type,
                "status": ogc_exc.status,
                "detail": ogc_exc.detail,
            },
        )
        # Store for handler to use
        context._ogc_exception = ogc_exc
        raise


def format_ogc_error_response(error: Exception) -> Dict[str, Any]:
    """Format an exception as OGC error response dict.

    Use this in handlers to return OGC-compliant error responses.
    """
    ogc_exc = convert_exception_to_ogc(error)
    return ogc_exc.to_dict()
