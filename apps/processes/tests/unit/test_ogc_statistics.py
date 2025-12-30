"""Unit tests for OGC statistics processes."""

import os
import sys

import pytest

sys.path.insert(0, "/app/apps/core/src")
sys.path.insert(0, "/app/apps/processes/src")

from lib.ogc_process_generator import (
    generate_process_description,
    generate_process_summary,
    get_process,
    get_process_list,
)
from lib.ogc_schemas import JobControlOptions, TransmissionMode
from lib.tool_registry import get_tool


# Base URL for tests - uses environment variables or defaults
TEST_HOST = os.environ.get("PROCESSES_HOST", "localhost")
TEST_PORT = os.environ.get("PROCESSES_PORT", "8200")
TEST_BASE_URL = f"http://{TEST_HOST}:{TEST_PORT}"


class TestStatisticsProcessDescriptions:
    """Test OGC process descriptions for statistics tools."""

    def test_feature_count_process_description(self):
        """Test feature_count process generates correct OGC description."""
        tool_info = get_tool("feature_count")
        assert tool_info is not None

        process = generate_process_description(tool_info, TEST_BASE_URL)

        # Basic info
        assert process.id == "feature_count"
        assert process.title == "Feature Count"
        assert process.version == "1.0.0"

        # Job control - should be sync only
        assert len(process.jobControlOptions) == 1
        assert JobControlOptions.sync_execute in process.jobControlOptions
        assert JobControlOptions.async_execute not in process.jobControlOptions

        # Inputs - should have collection, user_id, filter
        assert "collection" in process.inputs
        assert "user_id" in process.inputs
        assert "filter" in process.inputs

        # Outputs - should have count
        assert "count" in process.outputs
        assert process.outputs["count"].schema_["type"] == "integer"

    def test_unique_values_process_description(self):
        """Test unique_values process generates correct OGC description."""
        tool_info = get_tool("unique_values")
        assert tool_info is not None

        process = generate_process_description(tool_info, TEST_BASE_URL)

        # Basic info
        assert process.id == "unique_values"
        assert JobControlOptions.sync_execute in process.jobControlOptions

        # Inputs
        assert "collection" in process.inputs
        assert "attribute" in process.inputs
        assert "order" in process.inputs
        assert "limit" in process.inputs
        assert "offset" in process.inputs

        # Outputs
        assert "attribute" in process.outputs
        assert "total" in process.outputs
        assert "values" in process.outputs
        assert process.outputs["values"].schema_["type"] == "array"

    def test_class_breaks_process_description(self):
        """Test class_breaks process generates correct OGC description."""
        tool_info = get_tool("class_breaks")
        assert tool_info is not None

        process = generate_process_description(tool_info, TEST_BASE_URL)

        # Basic info
        assert process.id == "class_breaks"
        assert JobControlOptions.sync_execute in process.jobControlOptions

        # Inputs
        assert "collection" in process.inputs
        assert "attribute" in process.inputs
        assert "method" in process.inputs
        assert "breaks" in process.inputs
        assert "strip_zeros" in process.inputs

        # Outputs
        assert "attribute" in process.outputs
        assert "method" in process.outputs
        assert "breaks" in process.outputs
        assert "min" in process.outputs
        assert "max" in process.outputs
        assert "mean" in process.outputs
        assert "std_dev" in process.outputs

    def test_area_statistics_process_description(self):
        """Test area_statistics process generates correct OGC description."""
        tool_info = get_tool("area_statistics")
        assert tool_info is not None

        process = generate_process_description(tool_info, TEST_BASE_URL)

        # Basic info
        assert process.id == "area_statistics"
        assert JobControlOptions.sync_execute in process.jobControlOptions

        # Inputs
        assert "collection" in process.inputs
        assert "operation" in process.inputs

        # Outputs
        assert "result" in process.outputs
        assert "total_area" in process.outputs
        assert "feature_count" in process.outputs
        assert "unit" in process.outputs


class TestStatisticsProcessSummary:
    """Test OGC process summaries for statistics tools."""

    def test_statistics_tools_in_process_list(self):
        """Test that statistics tools appear in the process list."""
        processes = get_process_list(TEST_BASE_URL)
        process_ids = [p.id for p in processes]

        assert "feature_count" in process_ids
        assert "unique_values" in process_ids
        assert "class_breaks" in process_ids
        assert "area_statistics" in process_ids

    def test_statistics_summary_has_sync_execute(self):
        """Test that statistics process summaries have sync-execute."""
        stats_tools = ["feature_count", "unique_values", "class_breaks", "area_statistics"]

        for tool_name in stats_tools:
            tool_info = get_tool(tool_name)
            summary = generate_process_summary(tool_info, TEST_BASE_URL)

            assert JobControlOptions.sync_execute in summary.jobControlOptions
            assert JobControlOptions.async_execute not in summary.jobControlOptions


class TestVectorVsStatisticsProcesses:
    """Test differences between vector and statistics processes."""

    def test_vector_tools_have_async_execute(self):
        """Test that vector tools have async-execute job control."""
        tool_info = get_tool("clip")
        if tool_info is None:
            return  # Skip if clip not available

        process = generate_process_description(tool_info, TEST_BASE_URL)

        assert JobControlOptions.async_execute in process.jobControlOptions

    def test_statistics_outputs_are_not_layer_references(self):
        """Test that statistics outputs are direct values, not layer UUIDs."""
        # Statistics tools return results directly
        feature_count = get_process("feature_count", TEST_BASE_URL)
        assert feature_count is not None
        assert "count" in feature_count.outputs
        # Should be integer, not UUID
        assert feature_count.outputs["count"].schema_["type"] == "integer"

        # Vector tools return layer references
        clip = get_process("clip", TEST_BASE_URL)
        if clip is not None:
            assert "result" in clip.outputs
            # Should be UUID format
            assert clip.outputs["result"].schema_.get("format") == "uuid"


class TestProcessDescriptionSerialization:
    """Test OGC process description serialization."""

    def test_feature_count_serializes_correctly(self):
        """Test that feature_count process can be serialized to JSON."""
        process = get_process("feature_count", TEST_BASE_URL)
        assert process is not None

        # Should serialize without errors
        json_data = process.model_dump(by_alias=True, exclude_none=True)

        assert json_data["id"] == "feature_count"
        assert "sync-execute" in json_data["jobControlOptions"]
        assert "inputs" in json_data
        assert "outputs" in json_data

    def test_all_statistics_processes_serialize(self):
        """Test that all statistics processes can be serialized."""
        stats_tools = ["feature_count", "unique_values", "class_breaks", "area_statistics"]

        for tool_name in stats_tools:
            process = get_process(tool_name, TEST_BASE_URL)
            assert process is not None, f"{tool_name} process not found"

            # Should serialize without errors
            json_data = process.model_dump(by_alias=True, exclude_none=True)
            assert json_data["id"] == tool_name
            assert "sync-execute" in json_data["jobControlOptions"]
