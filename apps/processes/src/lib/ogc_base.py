"""Base utilities for OGC API Processes steps.

This module provides common functionality for all OGC API steps:
- URL building from request headers
- Standard response formatting with pydantic models
- OGC exception handling
"""

from typing import Any, Dict, Optional, TypeVar

from pydantic import BaseModel

from lib.config import settings
from lib.ogc_schemas import (
    OGC_EXCEPTION_INVALID_PARAMETER,
    OGC_EXCEPTION_NO_SUCH_JOB,
    OGC_EXCEPTION_NO_SUCH_PROCESS,
    Link,
    OGCException,
)

T = TypeVar("T", bound=BaseModel)


def get_base_url(req: Dict[str, Any]) -> str:
    """Build base URL from request headers with settings fallback.

    Args:
        req: Motia request dict with headers

    Returns:
        Base URL like "http://localhost:8200" or "https://api.example.com"
    """
    headers = req.get("headers", {})
    proto = headers.get("x-forwarded-proto", "http")
    host = headers.get("host", settings.default_host_port)
    return f"{proto}://{host}"


def pydantic_response(
    model: BaseModel, status: int = 200, headers: Optional[Dict[str, str]] = None
) -> Dict[str, Any]:
    """Create a response dict from a pydantic model.

    Args:
        model: Pydantic model to serialize
        status: HTTP status code
        headers: Optional response headers

    Returns:
        Motia response dict with status, body, and optional headers
    """
    response: Dict[str, Any] = {
        "status": status,
        "body": model.model_dump(by_alias=True, exclude_none=True),
    }
    if headers:
        response["headers"] = headers
    return response


def error_response(
    status: int,
    title: str,
    detail: str,
    exception_type: str = OGC_EXCEPTION_INVALID_PARAMETER,
) -> Dict[str, Any]:
    """Create an OGC-compliant error response.

    Args:
        status: HTTP status code
        title: Error title
        detail: Error detail message
        exception_type: OGC exception type URI

    Returns:
        Motia response dict with OGC exception body
    """
    error = OGCException(
        type=exception_type,
        title=title,
        status=status,
        detail=detail,
    )
    return {
        "status": status,
        "body": error.model_dump(),
    }


def not_found_response(resource_type: str, resource_id: str) -> Dict[str, Any]:
    """Create a 404 not found response.

    Args:
        resource_type: "process" or "job"
        resource_id: The ID that was not found

    Returns:
        Motia response dict with OGC exception
    """
    exception_type = (
        OGC_EXCEPTION_NO_SUCH_PROCESS
        if resource_type == "process"
        else OGC_EXCEPTION_NO_SUCH_JOB
    )
    return error_response(
        status=404,
        title=f"{resource_type.title()} not found",
        detail=f"{resource_type.title()} '{resource_id}' does not exist",
        exception_type=exception_type,
    )


def self_link(base_url: str, path: str, title: str = "This resource") -> Link:
    """Create a self-referencing link.

    Args:
        base_url: Base URL like "http://localhost:8200"
        path: Path like "/processes" or "/jobs/123"
        title: Link title

    Returns:
        Link model
    """
    return Link(
        href=f"{base_url}{path}",
        rel="self",
        type="application/json",
        title=title,
    )


# OGC Conformance classes for this implementation
PROCESSES_CONFORMANCE = [
    "http://www.opengis.net/spec/ogcapi-processes-1/1.0/conf/core",
    "http://www.opengis.net/spec/ogcapi-processes-1/1.0/conf/ogc-process-description",
    "http://www.opengis.net/spec/ogcapi-processes-1/1.0/conf/json",
    "http://www.opengis.net/spec/ogcapi-processes-1/1.0/conf/job-list",
    "http://www.opengis.net/spec/ogcapi-processes-1/1.0/conf/dismiss",
]
