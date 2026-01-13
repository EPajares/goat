"""Tests for OGC API Processes models."""

from datetime import datetime

from processes.models.processes import (
    OGC_EXCEPTION_INVALID_PARAMETER,
    OGC_EXCEPTION_NO_SUCH_PROCESS,
    ConformanceDeclaration,
    ExecuteRequest,
    InputDescription,
    JobControlOptions,
    JobList,
    Link,
    Metadata,
    OGCException,
    OutputDescription,
    ProcessDescription,
    ProcessList,
    ProcessSummary,
    ResponseType,
    StatusCode,
    StatusInfo,
    TransmissionMode,
)


class TestJobControlOptions:
    """Tests for JobControlOptions enum."""

    def test_sync_execute(self):
        assert JobControlOptions.sync_execute.value == "sync-execute"

    def test_async_execute(self):
        assert JobControlOptions.async_execute.value == "async-execute"

    def test_dismiss(self):
        assert JobControlOptions.dismiss.value == "dismiss"


class TestStatusCode:
    """Tests for StatusCode enum."""

    def test_all_status_codes(self):
        assert StatusCode.accepted.value == "accepted"
        assert StatusCode.running.value == "running"
        assert StatusCode.successful.value == "successful"
        assert StatusCode.failed.value == "failed"
        assert StatusCode.dismissed.value == "dismissed"


class TestTransmissionMode:
    """Tests for TransmissionMode enum."""

    def test_value_mode(self):
        assert TransmissionMode.value.value == "value"

    def test_reference_mode(self):
        assert TransmissionMode.reference.value == "reference"


class TestOGCException:
    """Tests for OGCException model."""

    def test_minimal_exception(self):
        exc = OGCException(title="Error", status=400)
        assert exc.title == "Error"
        assert exc.status == 400
        assert exc.type == OGC_EXCEPTION_INVALID_PARAMETER
        assert exc.detail is None

    def test_full_exception(self):
        exc = OGCException(
            type=OGC_EXCEPTION_NO_SUCH_PROCESS,
            title="Process not found",
            status=404,
            detail="The process 'xyz' does not exist",
            instance="/processes/xyz",
        )
        assert exc.type == OGC_EXCEPTION_NO_SUCH_PROCESS
        assert exc.detail == "The process 'xyz' does not exist"


class TestMetadata:
    """Tests for Metadata model."""

    def test_minimal_metadata(self):
        meta = Metadata(title="Test")
        assert meta.title == "Test"
        assert meta.role is None

    def test_geometry_constraint_metadata(self):
        meta = Metadata(
            title="Accepted Geometry Types",
            role="constraint",
        )
        assert meta.role == "constraint"


class TestInputDescription:
    """Tests for InputDescription model."""

    def test_minimal_input(self):
        inp = InputDescription(
            title="Input",
            schema={"type": "string"},
        )
        assert inp.title == "Input"
        assert inp.minOccurs == 1
        assert inp.maxOccurs == 1

    def test_optional_input(self):
        inp = InputDescription(
            title="Optional Input",
            schema={"type": "integer"},
            minOccurs=0,
        )
        assert inp.minOccurs == 0

    def test_array_input(self):
        inp = InputDescription(
            title="Multiple Values",
            schema={"type": "array", "items": {"type": "string"}},
            maxOccurs="unbounded",
        )
        assert inp.maxOccurs == "unbounded"


class TestOutputDescription:
    """Tests for OutputDescription model."""

    def test_output_description(self):
        out = OutputDescription(
            title="Result",
            schema={"type": "object"},
        )
        assert out.title == "Result"
        assert out.schema_ == {"type": "object"}


class TestProcessSummary:
    """Tests for ProcessSummary model."""

    def test_minimal_summary(self):
        """Test ProcessSummary with minimal required fields."""
        summary = ProcessSummary(
            id="feature-count",
            title="Feature Count",
            version="1.0.0",
        )
        assert summary.id == "feature-count"
        assert summary.title == "Feature Count"
        assert summary.version == "1.0.0"
        assert JobControlOptions.async_execute in summary.jobControlOptions

    def test_full_summary(self):
        summary = ProcessSummary(
            id="buffer",
            version="1.0.0",
            title="Buffer Tool",
            description="Create buffer around features",
            keywords=["analysis", "buffer"],
            links=[
                Link(href="/processes/buffer", rel="self", type="application/json"),
            ],
        )
        assert summary.title == "Buffer Tool"
        assert "analysis" in summary.keywords
        assert len(summary.links) == 1


class TestProcessDescription:
    """Tests for ProcessDescription model."""

    def test_process_description(self):
        desc = ProcessDescription(
            id="clip",
            version="1.0.0",
            title="Clip Tool",
            inputs={
                "input_layer": InputDescription(
                    title="Input Layer",
                    schema={"type": "string"},
                ),
                "clip_layer": InputDescription(
                    title="Clip Layer",
                    schema={"type": "string"},
                ),
            },
            outputs={
                "result": OutputDescription(
                    title="Clipped Features",
                    schema={"type": "object"},
                ),
            },
        )
        assert desc.id == "clip"
        assert "input_layer" in desc.inputs
        assert "result" in desc.outputs


class TestProcessList:
    """Tests for ProcessList model."""

    def test_empty_list(self):
        pl = ProcessList(processes=[], links=[])
        assert len(pl.processes) == 0

    def test_with_processes(self):
        pl = ProcessList(
            processes=[
                ProcessSummary(id="buffer", title="Buffer", version="1.0.0"),
                ProcessSummary(id="clip", title="Clip", version="1.0.0"),
            ],
            links=[
                Link(href="/processes", rel="self"),
            ],
        )
        assert len(pl.processes) == 2


class TestExecuteRequest:
    """Tests for ExecuteRequest model."""

    def test_minimal_request(self):
        req = ExecuteRequest(inputs={})
        assert req.inputs == {}
        # Default is document per OGC spec
        assert req.response == ResponseType.document

    def test_full_request(self):
        req = ExecuteRequest(
            inputs={
                "input_layer": "layer-123",
                "distance": 100,
            },
            outputs={"result": {}},
            response=ResponseType.document,
        )
        assert req.inputs["distance"] == 100
        assert req.response == ResponseType.document


class TestStatusInfo:
    """Tests for StatusInfo model."""

    def test_running_job(self):
        status = StatusInfo(
            processID="buffer",
            type="process",
            jobID="job-123",
            status=StatusCode.running,
            progress=50,
        )
        assert status.status == StatusCode.running
        assert status.progress == 50

    def test_completed_job(self):
        now = datetime.utcnow()
        status = StatusInfo(
            processID="clip",
            type="process",
            jobID="job-456",
            status=StatusCode.successful,
            progress=100,
            created=now,
            started=now,
            finished=now,
        )
        assert status.status == StatusCode.successful
        assert status.finished is not None


class TestJobList:
    """Tests for JobList model."""

    def test_empty_job_list(self):
        jobs = JobList(jobs=[], links=[])
        assert len(jobs.jobs) == 0

    def test_job_list_with_jobs(self):
        jobs = JobList(
            jobs=[
                StatusInfo(
                    processID="buffer",
                    type="process",
                    jobID="job-1",
                    status=StatusCode.running,
                ),
                StatusInfo(
                    processID="clip",
                    type="process",
                    jobID="job-2",
                    status=StatusCode.successful,
                ),
            ],
            links=[],
        )
        assert len(jobs.jobs) == 2


class TestConformanceDeclaration:
    """Tests for ConformanceDeclaration model."""

    def test_conformance(self):
        conf = ConformanceDeclaration(
            conformsTo=[
                "http://www.opengis.net/spec/ogcapi-processes-1/1.0/conf/core",
                "http://www.opengis.net/spec/ogcapi-processes-1/1.0/conf/json",
            ]
        )
        assert len(conf.conformsTo) == 2
        assert "core" in conf.conformsTo[0]
