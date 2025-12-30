"""Unit tests for the layer tool wrapper."""

from uuid import UUID, uuid4

import pytest

import sys; sys.path.insert(0, "/app/apps/processes/src")  # noqa: E702
import lib.paths  # noqa: F401 - sets up remaining paths

from core.storage.ducklake import ducklake_manager
from lib.layer_tool_wrapper import GenericLayerTool
from lib.tool_registry import get_tool


@pytest.mark.asyncio
async def test_clip_layer_with_filter_and_save(
    polygon_layer, boundary_layer, test_user
):
    """Test clipping layers with filter and saving result to DuckLake."""
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


@pytest.mark.asyncio
async def test_clip_layer_with_save_results_false(
    polygon_layer, boundary_layer, test_user
):
    """Test clipping layers with save_results=False returns presigned URL or parquet bytes."""
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
    print("[TEST] save_results=False - expecting presigned URL or parquet bytes")

    # Build params with save_results=False
    params = tool_info.layer_params_class(
        user_id=user_id,
        input_layer_id=input_layer_id,
        overlay_layer_id=overlay_layer_id,
        output_layer_id=output_layer_id,
        save_results=False,  # Don't save to DuckLake
    )

    # Create and run tool using GenericLayerTool wrapper
    wrapped_tool = GenericLayerTool(
        tool_class=tool_info.tool_class,
        params_class=tool_info.params_class,
        ducklake_manager=ducklake_manager,
    )
    result = wrapped_tool.run(params)

    # Verify result
    print(f"[TEST] Result: output_layer_id={result.output_layer_id}")
    print(f"[TEST] Result: download_url={result.download_url}")
    print(f"[TEST] Result: download_expires_at={result.download_expires_at}")
    print(
        f"[TEST] Result: parquet_bytes={len(result.parquet_bytes) if result.parquet_bytes else None}"
    )

    # Should NOT have output_layer_id (not saved to DuckLake)
    assert result.output_layer_id is None, "Should not save to DuckLake"

    # Should have either download_url or parquet_bytes
    if result.download_url:
        print(f"[TEST] SUCCESS: Got presigned URL: {result.download_url}")
        assert result.download_expires_at is not None
    else:
        # S3 not configured, should have parquet bytes as fallback
        print("[TEST] S3 not configured, got parquet bytes fallback")
        assert result.parquet_bytes is not None
        assert len(result.parquet_bytes) > 0


@pytest.mark.asyncio
async def test_join_layer_with_spatial_relationship(
    polygon_layer, boundary_layer, test_user
):
    """Test joining layers using spatial relationship and saving result to DuckLake."""
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
