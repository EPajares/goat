"""Unit tests for the tool registry."""

import lib.paths  # type: ignore # noqa: F401 - sets up sys.path

from lib.tool_registry import (
    get_all_tools,
    get_tool,
    get_tool_names,
    get_tools_metadata,
)


def test_get_clip_tool():
    """Test getting clip tool from registry."""
    tool_info = get_tool("clip")
    assert tool_info is not None
    assert tool_info.name == "clip"
    assert tool_info.display_name == "Clip"
    assert tool_info.category == "geoprocessing"
    # Verify auto-discovered classes (original and generated)
    assert tool_info.params_class.__name__ == "ClipParams"
    assert tool_info.layer_params_class.__name__ == "ClipLayerParams"
    assert tool_info.tool_class.__name__ == "ClipTool"


def test_get_tool_names():
    """Test getting all tool names."""
    names = get_tool_names()
    assert "clip" in names
    # With dynamic generation, we should have more tools
    assert "buffer" in names
    assert "centroid" in names


def test_auto_discovery():
    """Test that tools are auto-discovered from goatlib."""
    tools = get_all_tools()
    # With dynamic generation, we should have multiple tools
    assert len(tools) >= 5  # clip, buffer, centroid, intersection, etc.
    assert "clip" in tools

    # Verify each tool has required attributes
    for name, info in tools.items():
        assert info.name == name
        assert info.params_class is not None
        assert info.layer_params_class is not None
        assert info.tool_class is not None
        assert info.category in ("geoprocessing", "data_management", "statistics", "accessibility")


def test_tools_metadata():
    """Test getting tools metadata for API responses."""
    metadata = get_tools_metadata()
    assert len(metadata) >= 5

    clip_meta = next((m for m in metadata if m["name"] == "clip"), None)
    assert clip_meta is not None
    assert clip_meta["display_name"] == "Clip"
    assert "description" in clip_meta
    assert clip_meta["category"] == "geoprocessing"


def test_tools_metadata_with_schema():
    """Test getting tools metadata with JSON schema included."""
    metadata = get_tools_metadata(include_schema=True)
    assert len(metadata) >= 1

    clip_meta = next((m for m in metadata if m["name"] == "clip"), None)
    assert clip_meta is not None
    assert "schema" in clip_meta
    assert clip_meta["schema"]["type"] == "object"
    assert "properties" in clip_meta["schema"]

    props = clip_meta["schema"]["properties"]

    # Verify common fields are in schema
    assert "user_id" in props
    assert "project_id" in props
    assert "scenario_id" in props
    assert "save_results" in props

    # Verify layer-based fields are in schema (auto-generated)
    assert "input_layer_id" in props
    assert "overlay_layer_id" in props
    assert "input_filter" in props
    assert "overlay_filter" in props
    assert "output_layer_id" in props


def test_unknown_tool_returns_none():
    """Test that unknown tool returns None."""
    tool_info = get_tool("nonexistent_tool")
    assert tool_info is None


def test_join_layer_params_generation():
    """Test that JoinLayerParams is correctly generated from JoinParams."""
    tool_info = get_tool("join")
    assert tool_info is not None
    assert tool_info.name == "join"
    assert tool_info.layer_params_class.__name__ == "JoinLayerParams"

    # Check that path fields were transformed correctly
    fields = tool_info.layer_params_class.model_fields

    # Should have layer_id fields instead of path fields
    assert "target_layer_id" in fields, "target_path should become target_layer_id"
    assert "join_layer_id" in fields, "join_path should become join_layer_id"
    assert "output_layer_id" in fields, "output_path should become output_layer_id"

    # Should have filter fields for input layers (not output)
    assert "target_filter" in fields, "target should have a filter field"
    assert "join_filter" in fields, "join should have a filter field"

    # Should NOT have filter for output
    assert "output_filter" not in fields, "output should not have a filter field"

    # Should have user_id
    assert "user_id" in fields, "should have user_id field"

    # Should preserve non-path fields
    assert "use_spatial_relationship" in fields
    assert "use_attribute_relationship" in fields
    assert "join_operation" in fields


def test_layer_params_includes_project_scenario():
    """Test that LayerParams include project_id and scenario_id."""
    tool_info = get_tool("clip")
    assert tool_info is not None

    # Verify schema includes project_id and scenario_id
    fields = tool_info.layer_params_class.model_fields
    assert "project_id" in fields
    assert "scenario_id" in fields
    assert "save_results" in fields


# === Statistics Tool Tests ===


def test_feature_count_tool_registration():
    """Test that feature_count statistics tool is registered correctly."""
    tool_info = get_tool("feature_count")
    assert tool_info is not None
    assert tool_info.name == "feature_count"
    assert tool_info.display_name == "Feature Count"
    assert tool_info.category == "statistics"

    # Verify sync execution support
    assert tool_info.supports_sync is True
    assert tool_info.supports_async is False
    assert "sync-execute" in tool_info.job_control_options

    # Verify layer params include required fields
    fields = tool_info.layer_params_class.model_fields
    assert "collection" in fields
    assert "user_id" in fields
    assert "filter" in fields


def test_unique_values_tool_registration():
    """Test that unique_values statistics tool is registered correctly."""
    tool_info = get_tool("unique_values")
    assert tool_info is not None
    assert tool_info.name == "unique_values"
    assert tool_info.category == "statistics"
    assert tool_info.supports_sync is True

    # Verify layer params include required fields
    fields = tool_info.layer_params_class.model_fields
    assert "collection" in fields
    assert "user_id" in fields
    assert "attribute" in fields
    assert "order" in fields
    assert "limit" in fields
    assert "offset" in fields


def test_class_breaks_tool_registration():
    """Test that class_breaks statistics tool is registered correctly."""
    tool_info = get_tool("class_breaks")
    assert tool_info is not None
    assert tool_info.name == "class_breaks"
    assert tool_info.category == "statistics"
    assert tool_info.supports_sync is True

    # Verify layer params include required fields
    fields = tool_info.layer_params_class.model_fields
    assert "collection" in fields
    assert "user_id" in fields
    assert "attribute" in fields
    assert "method" in fields
    assert "breaks" in fields
    assert "strip_zeros" in fields


def test_area_statistics_tool_registration():
    """Test that area_statistics tool is registered correctly."""
    tool_info = get_tool("area_statistics")
    assert tool_info is not None
    assert tool_info.name == "area_statistics"
    assert tool_info.category == "statistics"
    assert tool_info.supports_sync is True

    # Verify layer params include required fields
    fields = tool_info.layer_params_class.model_fields
    assert "collection" in fields
    assert "user_id" in fields
    assert "operation" in fields


def test_statistics_tools_have_sync_execute():
    """Test that all statistics tools support sync execution only."""
    stats_tools = ["feature_count", "unique_values", "class_breaks", "area_statistics"]

    for tool_name in stats_tools:
        tool_info = get_tool(tool_name)
        assert tool_info is not None, f"{tool_name} not found"
        assert tool_info.supports_sync is True, f"{tool_name} should support sync"
        assert (
            tool_info.supports_async is False
        ), f"{tool_name} should not support async"
        assert tool_info.job_control_options == ["sync-execute"]


def test_vector_tools_have_async_execute():
    """Test that vector tools support async execution (default)."""
    vector_tools = ["clip", "buffer", "centroid"]

    for tool_name in vector_tools:
        tool_info = get_tool(tool_name)
        if tool_info is not None:  # Tool may not exist in all test environments
            assert tool_info.supports_async is True, f"{tool_name} should support async"
            assert "async-execute" in tool_info.job_control_options


def test_tools_metadata_includes_job_control():
    """Test that tools metadata includes job_control_options."""
    metadata = get_tools_metadata()

    # Find feature_count metadata
    fc_meta = next((m for m in metadata if m["name"] == "feature_count"), None)
    assert fc_meta is not None
    assert "job_control_options" in fc_meta
    assert fc_meta["job_control_options"] == ["sync-execute"]

    # Find clip metadata
    clip_meta = next((m for m in metadata if m["name"] == "clip"), None)
    if clip_meta:
        assert "job_control_options" in clip_meta
        assert "async-execute" in clip_meta["job_control_options"]
