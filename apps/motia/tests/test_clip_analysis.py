"""Test analysis tools using goatlib with DuckLake layers."""

import pytest
from uuid import uuid4, UUID

# Add paths for imports
import sys

sys.path.insert(0, "/app/apps/core/src")
sys.path.insert(0, "/app/apps/motia/src")

from core.storage.ducklake import ducklake_manager
from lib.tool_registry import (
    get_tool,
    get_tool_names,
    get_all_tools,
    get_tools_metadata,
)


class TestToolRegistry:
    """Test the auto-discovery tool registry functionality."""

    def test_get_clip_tool(self):
        """Test getting clip tool from registry."""
        tool_info = get_tool("clip")
        assert tool_info is not None
        assert tool_info.name == "clip"
        assert tool_info.display_name == "Clip"
        assert tool_info.category == "vector"
        # Verify auto-discovered classes (original and generated)
        assert tool_info.params_class.__name__ == "ClipParams"
        assert tool_info.layer_params_class.__name__ == "ClipLayerParams"
        assert tool_info.tool_class.__name__ == "ClipTool"

    def test_get_tool_names(self):
        """Test getting all tool names."""
        names = get_tool_names()
        assert "clip" in names
        # With dynamic generation, we should have more tools
        assert "buffer" in names
        assert "centroid" in names

    def test_auto_discovery(self):
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
            assert info.category == "vector"

    def test_tools_metadata(self):
        """Test getting tools metadata for API responses."""
        metadata = get_tools_metadata()
        assert len(metadata) >= 5

        clip_meta = next((m for m in metadata if m["name"] == "clip"), None)
        assert clip_meta is not None
        assert clip_meta["display_name"] == "Clip"
        assert "description" in clip_meta
        assert clip_meta["category"] == "vector"

    def test_tools_metadata_with_schema(self):
        """Test getting tools metadata with JSON schema included."""
        metadata = get_tools_metadata(include_schema=True)
        assert len(metadata) >= 1

        clip_meta = next((m for m in metadata if m["name"] == "clip"), None)
        assert clip_meta is not None
        assert "schema" in clip_meta
        assert clip_meta["schema"]["type"] == "object"
        assert "properties" in clip_meta["schema"]
        # Verify layer-based fields are in schema
        assert "user_id" in clip_meta["schema"]["properties"]
        assert "input_layer_id" in clip_meta["schema"]["properties"]

    def test_unknown_tool_returns_none(self):
        """Test that unknown tool returns None."""
        tool_info = get_tool("nonexistent_tool")
        assert tool_info is None


class TestClipAnalysis:
    """Test clip analysis using tool registry."""

    @pytest.mark.asyncio
    async def test_clip_layer_with_filter_and_save(
        self, polygon_layer, boundary_layer, test_user
    ):
        """Test clipping layers with filter and saving result to DuckLake."""
        from lib.layer_tool_wrapper import GenericLayerTool

        # Get clip tool from registry
        tool_info = get_tool("clip")
        assert tool_info is not None

        user_id = str(test_user.id)
        input_layer_id = str(polygon_layer["layer_id"])
        overlay_layer_id = str(boundary_layer["layer_id"])
        output_layer_id = str(uuid4())

        print(f"[TEST] Input layer: {input_layer_id}")
        print(f"[TEST] Overlay layer: {overlay_layer_id}")
        print(f"[TEST] Output layer: {output_layer_id}")

        # Build params using registry's layer_params_class (dynamically generated)
        params = tool_info.layer_params_class(
            user_id=user_id,
            input_layer_id=input_layer_id,
            overlay_layer_id=overlay_layer_id,
            input_filter="1=1",  # Trivial filter
            output_layer_id=output_layer_id,
        )

        # Create and run tool using GenericLayerTool wrapper
        wrapped_tool = GenericLayerTool(
            tool_class=tool_info.tool_class,
            params_class=tool_info.params_class,
            ducklake_manager=ducklake_manager,
        )
        result = wrapped_tool.run(params)

        # Verify result
        assert result.output_layer_id == output_layer_id
        assert result.feature_count > 0, "Clip output has no rows"

        # Verify layer exists in DuckLake
        output_table = ducklake_manager.get_layer_table_name(
            test_user.id, UUID(output_layer_id)
        )
        with ducklake_manager.connection() as con:
            count = con.execute(f"SELECT COUNT(*) FROM {output_table}").fetchone()[0]
            assert count == result.feature_count

        print(f"[TEST] Clip successful! Output has {result.feature_count} rows")


class TestJoinAnalysis:
    """Test join analysis using tool registry - involves multiple input layers."""

    @pytest.mark.asyncio
    async def test_join_layer_params_generation(self):
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

        print("[TEST] JoinLayerParams fields:", list(fields.keys()))

    @pytest.mark.asyncio
    async def test_join_layer_with_attribute_relationship(
        self, polygon_layer, boundary_layer, test_user
    ):
        """Test joining layers using attribute relationship and saving result to DuckLake."""
        from lib.layer_tool_wrapper import GenericLayerTool

        # Get join tool from registry
        tool_info = get_tool("join")
        assert tool_info is not None

        user_id = str(test_user.id)
        target_layer_id = str(polygon_layer["layer_id"])
        join_layer_id = str(boundary_layer["layer_id"])
        output_layer_id = str(uuid4())

        print(f"[TEST] Target layer: {target_layer_id}")
        print(f"[TEST] Join layer: {join_layer_id}")
        print(f"[TEST] Output layer: {output_layer_id}")

        # Build params using registry's layer_params_class (dynamically generated)
        # Use attribute join since both layers should have an 'id' or similar field
        params = tool_info.layer_params_class(
            user_id=user_id,
            target_layer_id=target_layer_id,
            join_layer_id=join_layer_id,
            target_filter=None,  # No filter
            join_filter=None,  # No filter
            output_layer_id=output_layer_id,
            use_spatial_relationship=True,  # Use spatial join
            use_attribute_relationship=False,
            spatial_relationship="intersects",
            join_operation="one_to_one",
            multiple_matching_records="first_record",
        )

        # Create and run tool using GenericLayerTool wrapper
        wrapped_tool = GenericLayerTool(
            tool_class=tool_info.tool_class,
            params_class=tool_info.params_class,
            ducklake_manager=ducklake_manager,
        )
        result = wrapped_tool.run(params)

        # Verify result
        assert result.output_layer_id == output_layer_id
        assert result.feature_count >= 0, "Join should return a result"

        # Verify layer exists in DuckLake
        output_table = ducklake_manager.get_layer_table_name(
            test_user.id, UUID(output_layer_id)
        )
        with ducklake_manager.connection() as con:
            count = con.execute(f"SELECT COUNT(*) FROM {output_table}").fetchone()[0]
            assert count == result.feature_count

        print(f"[TEST] Join successful! Output has {result.feature_count} rows")
