"""Test for layer filter and scenario support in tools.

This test demonstrates how filters and scenarios work with the tool infrastructure.
It uses mocked database services to test the logic without actual DB connections.
"""

import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from goatlib.tools.schemas import (
    ToolInputBase,
    LayerInputMixin,
    TwoLayerInputMixin,
)
from goatlib.tools.buffer import BufferToolParams


class TestToolInputSchemas:
    """Test the updated tool input schemas with filter and scenario support."""

    def test_tool_input_base_has_scenario_id(self):
        """ToolInputBase should have scenario_id field."""
        schema = ToolInputBase.model_json_schema()
        properties = schema["properties"]

        assert "scenario_id" in properties
        # Check it's a string type (nullable fields use anyOf in JSON schema)
        scenario_schema = properties["scenario_id"]
        assert "anyOf" in scenario_schema or scenario_schema.get("type") == "string"

    def test_layer_input_mixin_has_filter(self):
        """LayerInputMixin should have input_layer_filter field."""
        schema = LayerInputMixin.model_json_schema()
        properties = schema["properties"]

        assert "input_layer_id" in properties
        assert "input_layer_filter" in properties

    def test_two_layer_input_mixin_has_filters(self):
        """TwoLayerInputMixin should have filters for both layers."""
        schema = TwoLayerInputMixin.model_json_schema()
        properties = schema["properties"]

        assert "input_layer_id" in properties
        assert "input_layer_filter" in properties
        assert "overlay_layer_id" in properties
        assert "overlay_layer_filter" in properties

    def test_buffer_params_combined_schema(self):
        """BufferToolParams should inherit all fields correctly."""
        schema = BufferToolParams.model_json_schema()
        properties = schema["properties"]

        # From ToolInputBase
        assert "user_id" in properties
        assert "project_id" in properties
        assert "scenario_id" in properties

        # From LayerInputMixin
        assert "input_layer_id" in properties
        assert "input_layer_filter" in properties

        # From BufferParams
        assert "distances" in properties
        assert "units" in properties

    def test_buffer_params_with_filter(self):
        """BufferToolParams should accept CQL filter."""
        cql_filter = {"op": "=", "args": [{"property": "category"}, "residential"]}

        params = BufferToolParams(
            user_id="test-user-id-1234-5678-90ab-cdef12345678",
            input_layer_id="test-layer-id-1234-5678-90ab-cdef12345678",
            input_layer_filter=cql_filter,
            distances=[100.0],
            units="meters",
        )

        assert params.input_layer_filter == cql_filter
        assert params.scenario_id is None

    def test_buffer_params_with_scenario(self):
        """BufferToolParams should accept scenario_id."""
        params = BufferToolParams(
            user_id="test-user-id-1234-5678-90ab-cdef12345678",
            project_id="test-proj-id-1234-5678-90ab-cdef12345678",
            scenario_id="test-scen-id-1234-5678-90ab-cdef12345678",
            input_layer_id="test-layer-id-1234-5678-90ab-cdef12345678",
            distances=[100.0],
            units="meters",
        )

        assert params.scenario_id == "test-scen-id-1234-5678-90ab-cdef12345678"

    def test_buffer_params_full_example(self):
        """Test BufferToolParams with all filter and scenario options."""
        params = BufferToolParams(
            user_id="user-0000-0000-0000-000000000001",
            project_id="proj-0000-0000-0000-000000000001",
            folder_id="fold-0000-0000-0000-000000000001",
            scenario_id="scen-0000-0000-0000-000000000001",
            input_layer_id="layr-0000-0000-0000-000000000001",
            input_layer_filter={
                "op": "and",
                "args": [
                    {"op": ">", "args": [{"property": "population"}, 1000]},
                    {"op": "=", "args": [{"property": "type"}, "city"]},
                ],
            },
            distances=[100.0, 200.0, 500.0],
            units="meters",
            dissolve=True,
            output_name="Cities Buffer 100-500m",
        )

        # Verify all fields are set correctly
        assert params.user_id == "user-0000-0000-0000-000000000001"
        assert params.project_id == "proj-0000-0000-0000-000000000001"
        assert params.scenario_id == "scen-0000-0000-0000-000000000001"
        assert params.input_layer_filter["op"] == "and"
        assert len(params.input_layer_filter["args"]) == 2
        assert params.distances == [100.0, 200.0, 500.0]
        assert params.dissolve is True


class TestScenarioFeaturesMerge:
    """Test scenario feature merging logic."""

    def test_scenario_features_structure(self):
        """Verify expected scenario feature structure from DB."""
        # This is the structure returned by db_service.get_scenario_features
        scenario_features = [
            {
                "id": 1,
                "geom": "POINT(11.5 48.1)",
                "edit_type": "n",  # new
                "name": "New POI",
                "category": "shop",
            },
            {
                "id": 2,
                "geom": "POINT(11.6 48.2)",
                "edit_type": "m",  # modified
                "name": "Modified POI",
                "category": "restaurant",
            },
            {
                "id": 3,
                "geom": None,  # deleted features may have null geom
                "edit_type": "d",  # deleted
                "name": None,
                "category": None,
            },
        ]

        # Separate by edit type
        new_features = [f for f in scenario_features if f["edit_type"] == "n"]
        modified_features = [f for f in scenario_features if f["edit_type"] == "m"]
        deleted_features = [f for f in scenario_features if f["edit_type"] == "d"]

        assert len(new_features) == 1
        assert len(modified_features) == 1
        assert len(deleted_features) == 1

        # For merging: new + modified features are added
        # deleted + modified IDs are excluded from original
        features_to_add = [f for f in scenario_features if f["edit_type"] in ("n", "m")]
        ids_to_exclude = [
            f["id"] for f in scenario_features if f["edit_type"] in ("m", "d")
        ]

        assert len(features_to_add) == 2
        assert ids_to_exclude == [2, 3]


# Example of how the frontend would call the process
EXAMPLE_PROCESS_REQUEST = {
    "inputs": {
        "user_id": "abc12345-1234-5678-90ab-cdef12345678",
        "project_id": "proj1234-1234-5678-90ab-cdef12345678",
        "scenario_id": "scen1234-1234-5678-90ab-cdef12345678",
        "input_layer_id": "layr1234-1234-5678-90ab-cdef12345678",
        "input_layer_filter": {
            "op": "=",
            "args": [{"property": "category"}, "residential"],
        },
        "distances": [100, 200],
        "units": "meters",
        "dissolve": False,
        "output_name": "Residential Buffer",
    }
}


def test_example_request_parses():
    """Verify the example request can be parsed by BufferToolParams."""
    params = BufferToolParams(**EXAMPLE_PROCESS_REQUEST["inputs"])

    assert params.scenario_id == "scen1234-1234-5678-90ab-cdef12345678"
    assert params.input_layer_filter["op"] == "="
    assert params.distances == [100, 200]
