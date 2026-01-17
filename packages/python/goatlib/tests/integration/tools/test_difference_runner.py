"""Integration tests for DifferenceToolRunner.

Tests the complete DifferenceToolRunner workflow with real PostgreSQL and DuckLake.
DifferenceToolRunner is a two-layer input tool (input - overlay).

Unit tests for the difference analysis logic itself are in tests/unit/analysis/test_difference.py.

Run with:
    pytest tests/integration/tools/test_difference_runner.py -v
"""

import asyncio
from pathlib import Path

import pytest

from goatlib.tools.base import ToolSettings
from goatlib.tools.difference import DifferenceToolParams, DifferenceToolRunner

from .conftest import TEST_FOLDER_ID, TEST_USER_ID

pytestmark = pytest.mark.integration


@pytest.mark.asyncio(loop_scope="session")
class TestDifferenceToolRunner:
    """Integration tests for DifferenceToolRunner."""

    @pytest.fixture
    def runner(self, tool_settings: ToolSettings) -> DifferenceToolRunner:
        """Create a DifferenceToolRunner with test settings."""
        runner = DifferenceToolRunner()
        runner.init(tool_settings)
        return runner

    async def test_subtracts_overlay_from_input(
        self,
        runner: DifferenceToolRunner,
        create_layer_from_parquet,
        create_test_layer_metadata,
        verify_output_layer,
        cleanup_output_layer,
        vector_data_dir: Path,
    ):
        """Test DifferenceToolRunner subtracts overlay geometry from input."""
        # Setup: input layer (polygons)
        input_layer_id = create_layer_from_parquet(
            parquet_path=vector_data_dir / "overlay_polygons.parquet",
        )
        await create_test_layer_metadata(
            layer_id=input_layer_id,
            name="Input Polygons",
            geometry_type="polygon",
        )

        # Setup: overlay layer (area to subtract)
        overlay_layer_id = create_layer_from_parquet(
            parquet_path=vector_data_dir / "overlay_boundary.parquet",
        )
        await create_test_layer_metadata(
            layer_id=overlay_layer_id,
            name="Overlay Boundary",
            geometry_type="polygon",
        )

        # Run
        params = DifferenceToolParams(
            user_id=TEST_USER_ID,
            folder_id=TEST_FOLDER_ID,
            input_layer_id=input_layer_id,
            overlay_layer_id=overlay_layer_id,
            result_layer_name="Difference Result",
        )
        result = await asyncio.to_thread(runner.run, params)

        # Verify
        output_layer_id = await verify_output_layer(
            result=result,
            expected_name="Difference Result",
            min_features=0,  # Difference may result in 0 features
        )

        # Cleanup
        await cleanup_output_layer(output_layer_id)
