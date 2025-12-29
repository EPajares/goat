"""OGC API Processes models.

Implements OGC API - Processes - Part 1: Core (OGC 18-062r2)
https://docs.ogc.org/is/18-062r2/18-062r2.html
"""

from enum import Enum
from typing import Any

from goatlib.analysis.statistics import (
    AreaStatisticsInput as AreaStatisticsInputBase,
)
from goatlib.analysis.statistics import (
    AreaStatisticsResult,
    ClassBreaksResult,
    FeatureCountResult,
    UniqueValuesResult,
)
from goatlib.analysis.statistics import (
    ClassBreaksInput as ClassBreaksInputBase,
)
from goatlib.analysis.statistics import (
    FeatureCountInput as FeatureCountInputBase,
)
from goatlib.analysis.statistics import (
    UniqueValuesInput as UniqueValuesInputBase,
)
from pydantic import BaseModel, Field

from geoapi.models.ogc import Link


class JobControlOptions(str, Enum):
    """Execution modes supported by a process."""

    sync_execute = "sync-execute"
    async_execute = "async-execute"


class TransmissionMode(str, Enum):
    """How output values are transmitted."""

    value = "value"
    reference = "reference"


class StatusCode(str, Enum):
    """Job status codes."""

    accepted = "accepted"
    running = "running"
    successful = "successful"
    failed = "failed"
    dismissed = "dismissed"


class ResponseType(str, Enum):
    """Response format for process execution."""

    raw = "raw"
    document = "document"


# === Process Description Models ===


class ProcessSummary(BaseModel):
    """Summary of a process for listing."""

    id: str
    title: str
    description: str | None = None
    version: str = "1.0.0"
    jobControlOptions: list[JobControlOptions] = Field(
        default_factory=lambda: [JobControlOptions.sync_execute]
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

    class Config:
        populate_by_name = True


class OutputDescription(BaseModel):
    """Description of a process output."""

    title: str
    description: str | None = None
    schema_: dict[str, Any] = Field(alias="schema")

    class Config:
        populate_by_name = True


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


# === Result Models ===


class ResultDocument(BaseModel):
    """Result document containing process outputs."""

    # This uses additionalProperties pattern - outputs are keyed by output ID
    # For now we use a simple dict
    pass


# === Process-Specific Input/Output Models ===


class FeatureCountInput(FeatureCountInputBase):
    """Input for feature-count process."""

    collection: str = Field(description="Collection/layer ID (UUID)")


# Use FeatureCountResult from goatlib as output
FeatureCountOutput = FeatureCountResult


class AreaStatisticsInput(AreaStatisticsInputBase):
    """Input for area-statistics process."""

    collection: str = Field(description="Collection/layer ID (UUID)")


# Use AreaStatisticsResult from goatlib as output
AreaStatisticsOutput = AreaStatisticsResult


class UniqueValuesInput(UniqueValuesInputBase):
    """Input for unique-values process."""

    collection: str = Field(description="Collection/layer ID (UUID)")


# Use UniqueValuesResult from goatlib as output (UniqueValue is also from goatlib)
UniqueValuesOutput = UniqueValuesResult


class ClassBreaksInput(ClassBreaksInputBase):
    """Input for class-breaks process."""

    collection: str = Field(description="Collection/layer ID (UUID)")


# Use ClassBreaksResult from goatlib as output
ClassBreaksOutput = ClassBreaksResult
