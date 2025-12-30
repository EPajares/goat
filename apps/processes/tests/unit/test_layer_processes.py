"""Tests for OGC Layer Process definitions.

Tests:
- LayerImport, LayerExport, LayerUpdate process definitions
- Process registration in get_process_list
- Process retrieval via get_process
"""

# Add paths for imports
import sys

sys.path.insert(0, "/app/apps/core/src")
sys.path.insert(0, "/app/apps/processes/src")

import pytest

from lib.ogc_process_generator import (
    LAYER_PROCESSES,
    get_process,
    get_process_list,
)
from lib.ogc_schemas import JobControlOptions


class TestLayerProcessDefinitions:
    """Test static layer process definitions."""

    def test_layer_import_definition_exists(self):
        """Test LayerImport process definition exists."""
        assert "LayerImport" in LAYER_PROCESSES
        layer_import = LAYER_PROCESSES["LayerImport"]

        assert layer_import["title"] == "Layer Import"
        assert "description" in layer_import
        assert layer_import["version"] == "1.0.0"

    def test_layer_import_is_async_only(self):
        """Test LayerImport only supports async execution."""
        layer_import = LAYER_PROCESSES["LayerImport"]
        job_options = layer_import["jobControlOptions"]

        assert JobControlOptions.async_execute in job_options
        assert len(job_options) == 1  # Only async

    def test_layer_import_required_inputs(self):
        """Test LayerImport has required inputs."""
        inputs = LAYER_PROCESSES["LayerImport"]["inputs"]

        # Required inputs (minOccurs=1)
        assert inputs["layer_id"]["minOccurs"] == 1
        assert inputs["folder_id"]["minOccurs"] == 1
        assert inputs["name"]["minOccurs"] == 1

        # Optional inputs (minOccurs=0)
        assert inputs["s3_key"]["minOccurs"] == 0
        assert inputs["wfs_url"]["minOccurs"] == 0

    def test_layer_import_outputs(self):
        """Test LayerImport output definitions."""
        outputs = LAYER_PROCESSES["LayerImport"]["outputs"]

        assert "layer_id" in outputs
        assert "feature_count" in outputs
        assert "geometry_type" in outputs

    def test_layer_export_definition_exists(self):
        """Test LayerExport process definition exists."""
        assert "LayerExport" in LAYER_PROCESSES
        layer_export = LAYER_PROCESSES["LayerExport"]

        assert layer_export["title"] == "Layer Export"
        assert layer_export["version"] == "1.0.0"

    def test_layer_export_inputs(self):
        """Test LayerExport input definitions."""
        inputs = LAYER_PROCESSES["LayerExport"]["inputs"]

        # Required inputs
        assert inputs["layer_id"]["minOccurs"] == 1
        assert inputs["file_type"]["minOccurs"] == 1
        assert inputs["file_name"]["minOccurs"] == 1

        # Optional inputs
        assert inputs["crs"]["minOccurs"] == 0
        assert inputs["query"]["minOccurs"] == 0

        # File type enum
        file_type_schema = inputs["file_type"]["schema"]
        assert "enum" in file_type_schema
        assert "gpkg" in file_type_schema["enum"]
        assert "geojson" in file_type_schema["enum"]

    def test_layer_export_outputs(self):
        """Test LayerExport output definitions."""
        outputs = LAYER_PROCESSES["LayerExport"]["outputs"]

        assert "download_url" in outputs
        assert "s3_key" in outputs
        assert "file_size_bytes" in outputs

    def test_layer_update_definition_exists(self):
        """Test LayerUpdate process definition exists."""
        assert "LayerUpdate" in LAYER_PROCESSES
        layer_update = LAYER_PROCESSES["LayerUpdate"]

        assert layer_update["title"] == "Layer Update"
        assert layer_update["version"] == "1.0.0"

    def test_layer_update_inputs(self):
        """Test LayerUpdate input definitions."""
        inputs = LAYER_PROCESSES["LayerUpdate"]["inputs"]

        # Required
        assert inputs["layer_id"]["minOccurs"] == 1

        # Optional (one must be provided but both optional in schema)
        assert inputs["s3_key"]["minOccurs"] == 0
        assert inputs["refresh_wfs"]["minOccurs"] == 0

    def test_layer_update_outputs(self):
        """Test LayerUpdate output definitions."""
        outputs = LAYER_PROCESSES["LayerUpdate"]["outputs"]

        assert "feature_count" in outputs
        assert "geometry_type" in outputs


class TestLayerProcessRegistration:
    """Test layer processes are registered in process list."""

    def test_layer_processes_in_process_list(self):
        """Test layer processes appear in get_process_list."""
        process_list = get_process_list(base_url="http://test.local")

        # get_process_list returns List[ProcessSummary], not ProcessList
        process_ids = [p.id for p in process_list]

        assert "LayerImport" in process_ids
        assert "LayerExport" in process_ids
        assert "LayerUpdate" in process_ids

    def test_get_layer_import_process(self):
        """Test retrieving LayerImport process description."""
        process = get_process("LayerImport", base_url="http://test.local")

        assert process is not None
        assert process.id == "LayerImport"
        assert process.title == "Layer Import"
        assert len(process.inputs) > 0
        assert len(process.outputs) > 0

    def test_get_layer_export_process(self):
        """Test retrieving LayerExport process description."""
        process = get_process("LayerExport", base_url="http://test.local")

        assert process is not None
        assert process.id == "LayerExport"
        # inputs is a dict, not a list
        assert "layer_id" in process.inputs

    def test_get_layer_update_process(self):
        """Test retrieving LayerUpdate process description."""
        process = get_process("LayerUpdate", base_url="http://test.local")

        assert process is not None
        assert process.id == "LayerUpdate"
        assert JobControlOptions.async_execute in process.jobControlOptions


class TestLayerProcessSummaries:
    """Test layer process summary generation."""

    def test_layer_import_summary_in_list(self):
        """Test LayerImport summary appears correctly in list."""
        process_list = get_process_list(base_url="http://test.local")

        # process_list is List[ProcessSummary]
        layer_import = next(
            (p for p in process_list if p.id == "LayerImport"),
            None,
        )

        assert layer_import is not None
        assert layer_import.title == "Layer Import"
        assert "S3" in layer_import.description or "WFS" in layer_import.description
        assert layer_import.version == "1.0.0"

    def test_process_list_includes_analysis_and_layer(self):
        """Test process list includes both analysis and layer processes."""
        process_list = get_process_list(base_url="http://test.local")

        # process_list is List[ProcessSummary]
        process_ids = [p.id for p in process_list]

        # Layer processes
        assert "LayerImport" in process_ids
        assert "LayerExport" in process_ids
        assert "LayerUpdate" in process_ids

        # Analysis processes should also be there (from tool registry)
        # We don't require specific tools, just that the list isn't only layers
        assert len(process_ids) > 3
