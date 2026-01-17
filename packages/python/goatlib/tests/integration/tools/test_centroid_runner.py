"""Integration tests for CentroidToolRunner.

Tests the complete CentroidToolRunner workflow with real PostgreSQL and DuckLake.
CentroidToolRunner is a single-layer input tool.

Unit tests for the centroid analysis logic itself are in tests/unit/analysis/test_centroid.py.

Run with:
    pytest tests/integration/tools/test_centroid_runner.py -v
"""

import asyncio
from pathlib import Path

import pytest

from goatlib.tools.base import ToolSettings
from goatlib.tools.centroid import CentroidToolParams, CentroidToolRunner

from .conftest import TEST_FOLDER_ID, TEST_USER_ID

pytestmark = pytest.mark.integration


@pytest.mark.asyncio(loop_scope="session")
class TestCentroidToolRunner:
    """Integration tests for CentroidToolRunner."""

    @pytest.fixture
    def runner(self, tool_settings: ToolSettings) -> CentroidToolRunner:
        """Create a CentroidToolRunner with test settings."""
        runner = CentroidToolRunner()
        runner.init(tool_settings)
        return runner

    async def test_creates_points_from_polygons(
        self,
        runner: CentroidToolRunner,
        create_layer_from_parquet,
        create_test_layer_metadata,
        verify_output_layer,
        cleanup_output_layer,
        vector_data_dir: Path,
    ):
        """Test CentroidToolRunner creates point centroids from polygon input."""
        # Setup
        input_layer_id = create_layer_from_parquet(
            parquet_path=vector_data_dir / "overlay_polygons.parquet",
        )
        await create_test_layer_metadata(
            layer_id=input_layer_id,
            name="Input Polygons",
            geometry_type="polygon",
        )

        # Run
        params = CentroidToolParams(
            user_id=TEST_USER_ID,
            folder_id=TEST_FOLDER_ID,
            input_layer_id=input_layer_id,
            result_layer_name="Polygon Centroids",
        )
        result = await asyncio.to_thread(runner.run, params)

        # Verify
        output_layer_id = await verify_output_layer(
            result=result,
            expected_name="Polygon Centroids",
            min_features=1,
            expected_geometry_type="POINT",
        )

        # Cleanup
        await cleanup_output_layer(output_layer_id)
