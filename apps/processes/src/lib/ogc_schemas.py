"""OGC API Processes models for Motia.

Adapted from geoapi/models/processes.py and geoapi/models/ogc.py.
Implements OGC API - Processes - Part 1: Core (OGC 18-062r2)
https://docs.ogc.org/is/18-062r2/18-062r2.html

Extended with:
- Metadata support for geometry type constraints
- Keywords field for input categorization
"""

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

# === Common OGC Models ===


class Link(BaseModel):
    """OGC API Link."""

    href: str
    rel: str
    type: str | None = None
    title: str | None = None
    templated: bool | None = None


class GeometryType(str, Enum):
    """Geometry types."""

    point = "Point"
    line = "LineString"
    polygon = "Polygon"
    multipoint = "MultiPoint"
    multiline = "MultiLineString"
    multipolygon = "MultiPolygon"


# === Process Enums ===


class JobControlOptions(str, Enum):
    """Execution modes supported by a process."""

    sync_execute = "sync-execute"
    async_execute = "async-execute"


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


# === Metadata Models (Extended for geometry constraints) ===


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
    value: Any | None = None  # Can be list of geometry types, etc.


# === Process Description Models ===


class ProcessSummary(BaseModel):
    """Summary of a process for listing."""

    id: str
    title: str
    description: str | None = None
    version: str = "1.0.0"
    keywords: list[str] = Field(
        default_factory=list,
        description="Keywords/categories for the process (e.g., geoprocessing, data_management, statistics)",
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
    """Description of a process input.

    Extended with:
    - keywords: categorize inputs (e.g., ["geometry"] for layer inputs)
    - metadata: convey constraints like accepted geometry types
    """

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
    response: ResponseType = ResponseType.raw


# === Job Status Models ===


class StatusInfo(BaseModel):
    """Status information for a job."""

    processID: str | None = None
    type: str = "process"
    jobID: str
    status: StatusCode
    message: str | None = None
    created: str | None = None
    started: str | None = None
    finished: str | None = None
    updated: str | None = None
    progress: int | None = Field(default=None, ge=0, le=100)
    links: list[Link] = Field(default_factory=list)


class JobList(BaseModel):
    """List of jobs."""

    jobs: list[StatusInfo]
    links: list[Link] = Field(default_factory=list)


# === Landing Page & Conformance ===


class LandingPage(BaseModel):
    """Landing page response."""

    title: str
    description: str | None = None
    links: list[Link] = Field(default_factory=list)


class Conformance(BaseModel):
    """Conformance classes declaration."""

    conformsTo: list[str]


# === OGC Exception Models ===


class OGCException(BaseModel):
    """OGC API exception response.

    Per OGC API - Processes spec for error responses.
    """

    type: str  # URI like "http://www.opengis.net/def/exceptions/ogcapi-processes-1/1.0/InvalidParameterValue"
    title: str
    status: int
    detail: str | None = None
    instance: str | None = None


# === Constants ===

# Conformance classes for OGC API Processes
PROCESSES_CONFORMANCE = [
    "http://www.opengis.net/spec/ogcapi-processes-1/1.0/conf/core",
    "http://www.opengis.net/spec/ogcapi-processes-1/1.0/conf/ogc-process-description",
    "http://www.opengis.net/spec/ogcapi-processes-1/1.0/conf/json",
    "http://www.opengis.net/spec/ogcapi-processes-1/1.0/conf/job-list",
    "http://www.opengis.net/spec/ogcapi-processes-1/1.0/conf/dismiss",
]

# OGC Exception URIs
OGC_EXCEPTION_INVALID_PARAMETER = (
    "http://www.opengis.net/def/exceptions/ogcapi-processes-1/1.0/InvalidParameterValue"
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
OGC_EXCEPTION_EXECUTION_FAILED = (
    "http://www.opengis.net/def/exceptions/ogcapi-processes-1/1.0/execution-failed"
)
