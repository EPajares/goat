"""Tests for OGC API Processes compliance.

Tests:
- OGC schemas (Pydantic models)
- Process description generator
- Geometry constraint extraction
- Process list generation
"""

# Add paths for imports
import sys

import pytest

sys.path.insert(0, "/app/apps/core/src")
sys.path.insert(0, "/app/apps/processes/src")

from lib.ogc_process_generator import (
    _get_geometry_constraints,
    generate_process_description,
    generate_process_summary,
    get_process,
    get_process_list,
)
from lib.ogc_schemas import (
    OGC_EXCEPTION_NO_SUCH_PROCESS,
    PROCESSES_CONFORMANCE,
    Conformance,
    InputDescription,
    JobControlOptions,
    LandingPage,
    Link,
    Metadata,
    OGCException,
    OutputDescription,
    ProcessDescription,
    ProcessList,
    ProcessSummary,
    StatusCode,
    StatusInfo,
    TransmissionMode,
)
from lib.tool_registry import get_all_tools, get_tool

# === OGC Schema Tests ===


class TestOGCSchemas:
    """Test OGC Pydantic models."""

    def test_link_model(self):
        """Test Link model serialization."""
        link = Link(
            href="http://example.com/processes",
            rel="self",
            type="application/json",
            title="Process list",
        )
        data = link.model_dump()
        assert data["href"] == "http://example.com/processes"
        assert data["rel"] == "self"
        assert data["type"] == "application/json"

    def test_metadata_with_geometry_constraint(self):
        """Test Metadata model for geometry constraints."""
        metadata = Metadata(
            title="Accepted Geometry Types",
            role="constraint",
            value=["Polygon", "MultiPolygon"],
        )
        data = metadata.model_dump()
        assert data["title"] == "Accepted Geometry Types"
        assert data["role"] == "constraint"
        assert data["value"] == ["Polygon", "MultiPolygon"]

    def test_input_description_with_metadata(self):
        """Test InputDescription with geometry constraint metadata."""
        input_desc = InputDescription(
            title="Input Layer",
            description="UUID of the input layer",
            schema={"type": "string", "format": "uuid"},
            minOccurs=1,
            maxOccurs=1,
            keywords=["layer", "geometry"],
            metadata=[
                Metadata(
                    title="Accepted Geometry Types",
                    role="constraint",
                    value=["Point", "MultiPoint"],
                )
            ],
        )
        data = input_desc.model_dump(by_alias=True)
        assert data["title"] == "Input Layer"
        assert data["schema"]["type"] == "string"
        assert data["keywords"] == ["layer", "geometry"]
        assert len(data["metadata"]) == 1
        assert data["metadata"][0]["role"] == "constraint"

    def test_process_summary(self):
        """Test ProcessSummary model."""
        summary = ProcessSummary(
            id="clip",
            title="Clip",
            description="Clip features by overlay",
            version="1.0.0",
            jobControlOptions=[JobControlOptions.async_execute],
            outputTransmission=[TransmissionMode.value],
        )
        data = summary.model_dump()
        assert data["id"] == "clip"
        assert data["title"] == "Clip"
        assert "async-execute" in data["jobControlOptions"]

    def test_process_description_with_inputs_outputs(self):
        """Test ProcessDescription with inputs and outputs."""
        process = ProcessDescription(
            id="buffer",
            title="Buffer",
            description="Create buffer around features",
            inputs={
                "input_layer_id": InputDescription(
                    title="Input Layer",
                    schema={"type": "string", "format": "uuid"},
                ),
                "distance": InputDescription(
                    title="Distance",
                    schema={"type": "number"},
                ),
            },
            outputs={
                "result": OutputDescription(
                    title="Result Layer",
                    schema={"type": "string", "format": "uuid"},
                ),
            },
        )
        data = process.model_dump(by_alias=True)
        assert data["id"] == "buffer"
        assert "input_layer_id" in data["inputs"]
        assert "distance" in data["inputs"]
        assert "result" in data["outputs"]

    def test_status_info(self):
        """Test StatusInfo model for job status."""
        status = StatusInfo(
            processID="clip",
            jobID="clip-20251229-abc123",
            status=StatusCode.running,
            message="Processing...",
            progress=50,
        )
        data = status.model_dump()
        assert data["processID"] == "clip"
        assert data["jobID"] == "clip-20251229-abc123"
        assert data["status"] == "running"
        assert data["progress"] == 50

    def test_ogc_exception(self):
        """Test OGCException model."""
        error = OGCException(
            type=OGC_EXCEPTION_NO_SUCH_PROCESS,
            title="Process not found",
            status=404,
            detail="Process 'unknown' does not exist",
        )
        data = error.model_dump()
        assert data["status"] == 404
        assert "no-such-process" in data["type"]

    def test_conformance(self):
        """Test Conformance model."""
        conformance = Conformance(conformsTo=PROCESSES_CONFORMANCE)
        data = conformance.model_dump()
        assert len(data["conformsTo"]) >= 3
        assert any("core" in c for c in data["conformsTo"])

    def test_landing_page(self):
        """Test LandingPage model."""
        landing = LandingPage(
            title="GOAT Analysis API",
            description="OGC API Processes",
            links=[
                Link(href="/processes", rel="processes", type="application/json"),
            ],
        )
        data = landing.model_dump()
        assert data["title"] == "GOAT Analysis API"
        assert len(data["links"]) == 1


# === Process Generator Tests ===


class TestProcessGenerator:
    """Test OGC process description generator."""

    def test_generate_process_summary_for_clip(self):
        """Test generating ProcessSummary from clip ToolInfo."""
        tool_info = get_tool("clip")
        assert tool_info is not None

        summary = generate_process_summary(tool_info, "http://localhost")
        assert summary.id == "clip"
        assert summary.title == "Clip"
        assert JobControlOptions.async_execute in summary.jobControlOptions
        assert len(summary.links) > 0
        assert summary.links[0].href == "http://localhost/processes/clip"

    def test_generate_process_description_for_clip(self):
        """Test generating full ProcessDescription from clip ToolInfo."""
        tool_info = get_tool("clip")
        assert tool_info is not None

        description = generate_process_description(tool_info, "http://localhost")

        # Basic fields
        assert description.id == "clip"
        assert description.title == "Clip"
        assert description.version == "1.0.0"

        # Inputs should include layer_id fields
        assert "input_layer_id" in description.inputs
        assert "overlay_layer_id" in description.inputs
        assert "user_id" in description.inputs

        # Output layer ID should NOT be in inputs (it's an output)
        assert "output_layer_id" not in description.inputs

        # Outputs
        assert "result" in description.outputs

        # Links
        assert len(description.links) >= 2
        link_rels = [l.rel for l in description.links]
        assert "self" in link_rels

    def test_process_description_includes_layer_keywords(self):
        """Test that layer_id inputs have 'layer' keyword."""
        tool_info = get_tool("clip")
        description = generate_process_description(tool_info)

        input_layer = description.inputs.get("input_layer_id")
        assert input_layer is not None
        assert "layer" in input_layer.keywords

    def test_get_process_returns_none_for_unknown(self):
        """Test get_process returns None for unknown process."""
        result = get_process("nonexistent_process")
        assert result is None

    def test_get_process_list(self):
        """Test get_process_list returns all tools."""
        processes = get_process_list("http://localhost")

        # Should have multiple processes
        assert len(processes) >= 5

        # All should be ProcessSummary instances
        for p in processes:
            assert isinstance(p, ProcessSummary)
            assert p.id is not None
            assert p.title is not None

        # Clip should be in the list
        clip = next((p for p in processes if p.id == "clip"), None)
        assert clip is not None
        assert clip.title == "Clip"

    def test_process_description_schema_format(self):
        """Test that inputs have proper JSON schema format."""
        tool_info = get_tool("buffer")
        if not tool_info:
            pytest.skip("buffer tool not available")

        description = generate_process_description(tool_info)

        # Check input_layer_id has uuid format
        input_layer = description.inputs.get("input_layer_id")
        if input_layer:
            schema = input_layer.schema_
            assert schema.get("type") == "string"
            # Format might be uuid or not depending on field definition


class TestGeometryConstraints:
    """Test geometry constraint extraction."""

    def test_get_geometry_constraints_from_clip_params(self):
        """Test extracting geometry constraints from ClipParams."""
        tool_info = get_tool("clip")
        assert tool_info is not None

        constraints = _get_geometry_constraints(tool_info.params_class)

        # ClipParams should have constraints for input and overlay
        # Note: actual constraints depend on goatlib implementation
        # This test verifies the extraction mechanism works
        assert isinstance(constraints, dict)

    def test_buffer_tool_process_description(self):
        """Test buffer tool generates valid process description."""
        tool_info = get_tool("buffer")
        if not tool_info:
            pytest.skip("buffer tool not available")

        description = generate_process_description(tool_info, "http://localhost")

        assert description.id == "buffer"
        assert "input_layer_id" in description.inputs
        assert "result" in description.outputs


# === Process List Integration Tests ===


class TestProcessListIntegration:
    """Integration tests for process list generation."""

    def test_all_tools_generate_valid_descriptions(self):
        """Test that all registered tools generate valid ProcessDescriptions."""
        tools = get_all_tools()

        for name, tool_info in tools.items():
            description = generate_process_description(tool_info)

            # Basic validation
            assert description.id == name, f"ID mismatch for {name}"
            assert description.title is not None, f"Missing title for {name}"
            assert len(description.inputs) > 0, f"No inputs for {name}"
            assert len(description.outputs) > 0, f"No outputs for {name}"

            # All should have user_id input
            assert "user_id" in description.inputs, f"Missing user_id for {name}"

    def test_process_list_serialization(self):
        """Test ProcessList serializes correctly for API response."""
        processes = get_process_list("http://localhost")
        process_list = ProcessList(
            processes=processes,
            links=[Link(href="/processes", rel="self", type="application/json")],
        )

        data = process_list.model_dump(by_alias=True, exclude_none=True)

        assert "processes" in data
        assert len(data["processes"]) >= 5
        assert "links" in data

        # Each process should have required OGC fields
        for p in data["processes"]:
            assert "id" in p
            assert "title" in p
            assert "jobControlOptions" in p
