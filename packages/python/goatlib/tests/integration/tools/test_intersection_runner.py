"""Integration tests for IntersectionToolRunner.

Tests the complete IntersectionToolRunner workflow with real PostgreSQL and DuckLake.
IntersectionToolRunner is a two-layer input tool (input + overlay).

Unit tests for the intersection analysis logic itself are in tests/unit/analysis/test_intersection.py.

Run with:
    pytest tests/integration/tools/test_intersection_runner.py -v
"""

import asyncio
from pathlib import Path

import pytest

from goatlib.tools.base import ToolSettings
from goatlib.tools.intersection import IntersectionToolParams, IntersectionToolRunner

from .conftest import TEST_FOLDER_ID, TEST_USER_ID

pytestmark = pytest.mark.integration


@pytest.mark.asyncio(loop_scope="session")
class TestIntersectionToolRunner:
    """Integration tests for IntersectionToolRunner."""

    @pytest.fixture
    def runner(self, tool_settings: ToolSettings) -> IntersectionToolRunner:
        """Create an IntersectionToolRunner with test settings."""
        runner = IntersectionToolRunner()
        runner.init(tool_settings)
        return runner

    async def test_intersects_two_polygon_layers(
        self,
        runner: IntersectionToolRunner,
        create_layer_from_parquet,
        create_test_layer_metadata,
        verify_output_layer,
        cleanup_output_layer,
        vector_data_dir: Path,
    ):
        """Test IntersectionToolRunner computes intersection of two polygon layers."""
        # Setup: input layer (polygons)
        input_layer_id = create_layer_from_parquet(
            parquet_path=vector_data_dir / "overlay_polygons.parquet",
        )
        await create_test_layer_metadata(
            layer_id=input_layer_id,
            name="Input Polygons",
            geometry_type="polygon",
        )

        # Setup: overlay layer (boundary polygon)
        overlay_layer_id = create_layer_from_parquet(
            parquet_path=vector_data_dir / "overlay_boundary.parquet",
        )
        await create_test_layer_metadata(
            layer_id=overlay_layer_id,
            name="Overlay Boundary",
            geometry_type="polygon",
        )

        # Run
        params = IntersectionToolParams(
            user_id=TEST_USER_ID,
            folder_id=TEST_FOLDER_ID,
            input_layer_id=input_layer_id,
            overlay_layer_id=overlay_layer_id,
            result_layer_name="Intersection Result",
        )
        result = await asyncio.to_thread(runner.run, params)

        # Verify
        output_layer_id = await verify_output_layer(
            result=result,
            expected_name="Intersection Result",
            min_features=0,  # Intersection may have 0 features
        )

        # Cleanup
        await cleanup_output_layer(output_layer_id)
