"""Integration tests for UnionToolRunner.

Tests the complete UnionToolRunner workflow with real PostgreSQL and DuckLake.
UnionToolRunner supports both self-union (single layer) and two-layer union.

Unit tests for the union analysis logic itself are in tests/unit/analysis/test_union.py.

Run with:
    pytest tests/integration/tools/test_union_runner.py -v
"""

import asyncio
from pathlib import Path

import pytest

from goatlib.tools.base import ToolSettings
from goatlib.tools.union import UnionToolParams, UnionToolRunner

from .conftest import TEST_FOLDER_ID, TEST_USER_ID

pytestmark = pytest.mark.integration


@pytest.mark.asyncio(loop_scope="session")
class TestUnionToolRunner:
    """Integration tests for UnionToolRunner."""

    @pytest.fixture
    def runner(self, tool_settings: ToolSettings) -> UnionToolRunner:
        """Create a UnionToolRunner with test settings."""
        runner = UnionToolRunner()
        runner.init(tool_settings)
        return runner

    async def test_self_union_creates_layer(
        self,
        runner: UnionToolRunner,
        create_layer_from_parquet,
        create_test_layer_metadata,
        verify_output_layer,
        cleanup_output_layer,
        vector_data_dir: Path,
    ):
        """Test UnionToolRunner with self-union (single layer)."""
        # Setup
        input_layer_id = create_layer_from_parquet(
            parquet_path=vector_data_dir / "overlay_polygons.parquet",
        )
        await create_test_layer_metadata(
            layer_id=input_layer_id,
            name="Input Polygons",
            geometry_type="polygon",
        )

        # Run self-union (no overlay_layer_id)
        params = UnionToolParams(
            user_id=TEST_USER_ID,
            folder_id=TEST_FOLDER_ID,
            input_layer_id=input_layer_id,
            result_layer_name="Self Union Result",
        )
        result = await asyncio.to_thread(runner.run, params)

        # Verify
        output_layer_id = await verify_output_layer(
            result=result,
            expected_name="Self Union Result",
            min_features=1,
        )

        # Cleanup
        await cleanup_output_layer(output_layer_id)

    async def test_two_layer_union_creates_layer(
        self,
        runner: UnionToolRunner,
        create_layer_from_parquet,
        create_test_layer_metadata,
        verify_output_layer,
        cleanup_output_layer,
        vector_data_dir: Path,
    ):
        """Test UnionToolRunner with two input layers."""
        # Setup: input layer
        input_layer_id = create_layer_from_parquet(
            parquet_path=vector_data_dir / "overlay_polygons.parquet",
        )
        await create_test_layer_metadata(
            layer_id=input_layer_id,
            name="Input Polygons",
            geometry_type="polygon",
        )

        # Setup: overlay layer
        overlay_layer_id = create_layer_from_parquet(
            parquet_path=vector_data_dir / "overlay_boundary.parquet",
        )
        await create_test_layer_metadata(
            layer_id=overlay_layer_id,
            name="Overlay Boundary",
            geometry_type="polygon",
        )

        # Run two-layer union
        params = UnionToolParams(
            user_id=TEST_USER_ID,
            folder_id=TEST_FOLDER_ID,
            input_layer_id=input_layer_id,
            overlay_layer_id=overlay_layer_id,
            result_layer_name="Two Layer Union",
        )
        result = await asyncio.to_thread(runner.run, params)

        # Verify
        output_layer_id = await verify_output_layer(
            result=result,
            expected_name="Two Layer Union",
            min_features=1,
        )

        # Cleanup
        await cleanup_output_layer(output_layer_id)
