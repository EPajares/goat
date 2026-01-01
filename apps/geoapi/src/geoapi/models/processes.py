"""OGC API Processes models.

Implements OGC API - Processes - Part 1: Core (OGC 18-062r2)
https://docs.ogc.org/is/18-062r2/18-062r2.html

Extended with:
- Metadata support for geometry type constraints
- Keywords field for input categorization
"""

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

# Import shared models from ogc.py to avoid duplication
from geoapi.models.ogc import Link

# === Process Enums ===


class JobControlOptions(str, Enum):
    """Execution modes supported by a process."""

    sync_execute = "sync-execute"
    async_execute = "async-execute"
    dismiss = "dismiss"


class TransmissionMode(str, Enum):
    """How output values are transmitted."""

    value = "value"
    reference = "reference"


class StatusCode(str, Enum):
    """OGC job status codes."""

    accepted = "accepted"
    running = "running"
    successful = "successful"
    failed = "failed"
    dismissed = "dismissed"


class ResponseType(str, Enum):
    """Response format for process execution."""

    raw = "raw"
    document = "document"


# === OGC Exception ===


# Exception type URIs
OGC_EXCEPTION_INVALID_PARAMETER = (
    "http://www.opengis.net/def/exceptions/ogcapi-processes-1/1.0/invalid-parameter"
)
OGC_EXCEPTION_NO_SUCH_PROCESS = (
    "http://www.opengis.net/def/exceptions/ogcapi-processes-1/1.0/no-such-process"
)
OGC_EXCEPTION_NO_SUCH_JOB = (
    "http://www.opengis.net/def/exceptions/ogcapi-processes-1/1.0/no-such-job"
)
OGC_EXCEPTION_RESULT_NOT_READY = (
    "http://www.opengis.net/def/exceptions/ogcapi-processes-1/1.0/result-not-ready"
)


class OGCException(BaseModel):
    """OGC API exception response (RFC 7807 compatible)."""

    type: str = OGC_EXCEPTION_INVALID_PARAMETER
    title: str
    status: int
    detail: str | None = None
    instance: str | None = None


# === Metadata Models ===


class Metadata(BaseModel):
    """Metadata entry for input/output descriptions.

    Used to convey geometry type constraints per OGC spec.
    Example:
        {
            "title": "Accepted Geometry Types",
            "role": "constraint",
            "value": ["Polygon", "MultiPolygon"]
        }
    """

    title: str
    role: str | None = None
    href: str | None = None
    value: Any | None = None


# === Process Description Models ===


class ProcessSummary(BaseModel):
    """Summary of a process for listing."""

    id: str
    title: str
    description: str | None = None
    version: str = "1.0.0"
    keywords: list[str] = Field(
        default_factory=list,
        description="Keywords/categories for the process",
    )
    jobControlOptions: list[JobControlOptions] = Field(
        default_factory=lambda: [JobControlOptions.async_execute]
    )
    outputTransmission: list[TransmissionMode] = Field(
        default_factory=lambda: [TransmissionMode.value]
    )
    links: list[Link] = Field(default_factory=list)


class ProcessList(BaseModel):
    """List of available processes."""

    processes: list[ProcessSummary]
    links: list[Link] = Field(default_factory=list)


class InputDescription(BaseModel):
    """Description of a process input."""

    title: str
    description: str | None = None
    schema_: dict[str, Any] = Field(alias="schema")
    minOccurs: int = 1
    maxOccurs: int | str = 1  # Can be "unbounded"
    keywords: list[str] = Field(default_factory=list)
    metadata: list[Metadata] = Field(default_factory=list)

    model_config = {"populate_by_name": True}


class OutputDescription(BaseModel):
    """Description of a process output."""

    title: str
    description: str | None = None
    schema_: dict[str, Any] = Field(alias="schema")

    model_config = {"populate_by_name": True}


class ProcessDescription(ProcessSummary):
    """Full description of a process with inputs/outputs."""

    inputs: dict[str, InputDescription] = Field(default_factory=dict)
    outputs: dict[str, OutputDescription] = Field(default_factory=dict)


# === Execution Models ===


class OutputDefinition(BaseModel):
    """Output specification in execute request."""

    transmissionMode: TransmissionMode = TransmissionMode.value
    format: dict[str, str] | None = None


class ExecuteRequest(BaseModel):
    """Request body for process execution."""

    inputs: dict[str, Any] = Field(default_factory=dict)
    outputs: dict[str, OutputDefinition] | None = None
    response: ResponseType = ResponseType.document


# === Job Status Models ===


class StatusInfo(BaseModel):
    """Status information for a job."""

    processID: str | None = None
    type: str = "process"
    jobID: str
    status: StatusCode
    message: str | None = None
    created: datetime | None = None
    started: datetime | None = None
    finished: datetime | None = None
    updated: datetime | None = None
    progress: int | None = Field(default=None, ge=0, le=100)
    links: list[Link] = Field(default_factory=list)


class JobList(BaseModel):
    """List of jobs."""

    jobs: list[StatusInfo]
    links: list[Link] = Field(default_factory=list)


# === Conformance ===


class ConformanceDeclaration(BaseModel):
    """Declaration of conformance classes."""

    conformsTo: list[str] = Field(default_factory=list)


# === Landing Page ===


class LandingPage(BaseModel):
    """API landing page."""

    title: str
    description: str | None = None
    links: list[Link] = Field(default_factory=list)
