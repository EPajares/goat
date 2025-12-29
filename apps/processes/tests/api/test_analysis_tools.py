"""Test analysis tools with DuckLake layer I/O."""

import sys
from uuid import UUID, uuid4

import pytest

sys.path.insert(0, "/app/apps/core/src")
sys.path.insert(0, "/app/apps/processes/src")

from core.storage.ducklake import ducklake_manager
from lib.tool_registry import get_tool


@pytest.mark.asyncio
async def test_clip_layer_with_filter_and_save(
    polygon_layer, boundary_layer, test_user
):
    """test clipping layers with filter and saving result to ducklake."""
    from lib.layer_tool_wrapper import GenericLayerTool

    tool_info = get_tool("clip")
    assert tool_info is not None

    user_id = str(test_user.id)
    input_layer_id = str(polygon_layer["layer_id"])
    overlay_layer_id = str(boundary_layer["layer_id"])
    output_layer_id = str(uuid4())

    print(f"[TEST] Input layer: {input_layer_id}")
    print(f"[TEST] Overlay layer: {overlay_layer_id}")
    print(f"[TEST] Output layer: {output_layer_id}")

    params = tool_info.layer_params_class(
        user_id=user_id,
        input_layer_id=input_layer_id,
        overlay_layer_id=overlay_layer_id,
        input_filter="1=1",
        output_layer_id=output_layer_id,
    )

    wrapped_tool = GenericLayerTool(
        tool_class=tool_info.tool_class,
        params_class=tool_info.params_class,
        ducklake_manager=ducklake_manager,
    )
    result = wrapped_tool.run(params)

    assert result.output_layer_id == output_layer_id
    assert result.feature_count > 0, "Clip output has no rows"

    output_table = ducklake_manager.get_layer_table_name(
        test_user.id, UUID(output_layer_id)
    )
    with ducklake_manager.connection() as con:
        count = con.execute(f"SELECT COUNT(*) FROM {output_table}").fetchone()[0]
        assert count == result.feature_count

    print(f"[TEST] Clip successful! Output has {result.feature_count} rows")


@pytest.mark.asyncio
async def test_join_layer_params_generation():
    """test that JoinLayerParams is correctly generated from JoinParams."""
    tool_info = get_tool("join")
    assert tool_info is not None
    assert tool_info.name == "join"
    assert tool_info.layer_params_class.__name__ == "JoinLayerParams"

    fields = tool_info.layer_params_class.model_fields

    # Should have layer_id fields instead of path fields
    assert "target_layer_id" in fields, "target_path should become target_layer_id"
    assert "join_layer_id" in fields, "join_path should become join_layer_id"
    assert "output_layer_id" in fields, "output_path should become output_layer_id"

    # Should have filter fields for input layers (not output)
    assert "target_filter" in fields, "target should have a filter field"
    assert "join_filter" in fields, "join should have a filter field"
    assert "output_filter" not in fields, "output should not have a filter field"

    # Should have user_id and preserve non-path fields
    assert "user_id" in fields, "should have user_id field"
    assert "use_spatial_relationship" in fields
    assert "use_attribute_relationship" in fields
    assert "join_operation" in fields

    print("[TEST] JoinLayerParams fields:", list(fields.keys()))


@pytest.mark.asyncio
async def test_join_layer_with_spatial_relationship(
    polygon_layer, boundary_layer, test_user
):
    """test joining layers using spatial relationship and saving result to ducklake."""
    from lib.layer_tool_wrapper import GenericLayerTool

    tool_info = get_tool("join")
    assert tool_info is not None

    user_id = str(test_user.id)
    target_layer_id = str(polygon_layer["layer_id"])
    join_layer_id = str(boundary_layer["layer_id"])
    output_layer_id = str(uuid4())

    print(f"[TEST] Target layer: {target_layer_id}")
    print(f"[TEST] Join layer: {join_layer_id}")
    print(f"[TEST] Output layer: {output_layer_id}")

    params = tool_info.layer_params_class(
        user_id=user_id,
        target_layer_id=target_layer_id,
        join_layer_id=join_layer_id,
        target_filter=None,
        join_filter=None,
        output_layer_id=output_layer_id,
        use_spatial_relationship=True,
        use_attribute_relationship=False,
        spatial_relationship="intersects",
        join_operation="one_to_one",
        multiple_matching_records="first_record",
    )

    wrapped_tool = GenericLayerTool(
        tool_class=tool_info.tool_class,
        params_class=tool_info.params_class,
        ducklake_manager=ducklake_manager,
    )
    result = wrapped_tool.run(params)

    assert result.output_layer_id == output_layer_id
    assert result.feature_count >= 0, "Join should return a result"

    output_table = ducklake_manager.get_layer_table_name(
        test_user.id, UUID(output_layer_id)
    )
    with ducklake_manager.connection() as con:
        count = con.execute(f"SELECT COUNT(*) FROM {output_table}").fetchone()[0]
        assert count == result.feature_count

    print(f"[TEST] Join successful! Output has {result.feature_count} rows")
