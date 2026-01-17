"""Integration tests for ClipToolRunner.

Tests the complete ClipToolRunner workflow with real PostgreSQL and DuckLake.
ClipToolRunner is a two-layer input tool (input + overlay).

Unit tests for the clip analysis logic itself are in tests/unit/analysis/test_clip.py.

Run with:
    pytest tests/integration/tools/test_clip_runner.py -v
"""

import asyncio
from pathlib import Path

import pytest

from goatlib.tools.base import ToolSettings
from goatlib.tools.clip import ClipToolParams, ClipToolRunner

from .conftest import TEST_FOLDER_ID, TEST_USER_ID

pytestmark = pytest.mark.integration


@pytest.mark.asyncio(loop_scope="session")
class TestClipToolRunner:
    """Integration tests for ClipToolRunner."""

    @pytest.fixture
    def runner(self, tool_settings: ToolSettings) -> ClipToolRunner:
        """Create a ClipToolRunner with test settings."""
        runner = ClipToolRunner()
        runner.init(tool_settings)
        return runner

    async def test_clips_points_to_boundary(
        self,
        runner: ClipToolRunner,
        create_layer_from_parquet,
        create_test_layer_metadata,
        verify_output_layer,
        cleanup_output_layer,
        vector_data_dir: Path,
    ):
        """Test ClipToolRunner clips points to a polygon boundary."""
        # Setup: input layer (points to clip)
        input_layer_id = create_layer_from_parquet(
            parquet_path=vector_data_dir / "overlay_points.parquet",
        )
        await create_test_layer_metadata(
            layer_id=input_layer_id,
            name="Input Points",
            geometry_type="point",
        )

        # Setup: overlay layer (clipping boundary)
        overlay_layer_id = create_layer_from_parquet(
            parquet_path=vector_data_dir / "overlay_boundary.parquet",
        )
        await create_test_layer_metadata(
            layer_id=overlay_layer_id,
            name="Clip Boundary",
            geometry_type="polygon",
        )

        # Run
        params = ClipToolParams(
            user_id=TEST_USER_ID,
            folder_id=TEST_FOLDER_ID,
            input_layer_id=input_layer_id,
            overlay_layer_id=overlay_layer_id,
            result_layer_name="Clipped Points",
        )
        result = await asyncio.to_thread(runner.run, params)

        # Verify
        output_layer_id = await verify_output_layer(
            result=result,
            expected_name="Clipped Points",
            min_features=0,  # Clip may result in 0 features
        )

        # Cleanup
        await cleanup_output_layer(output_layer_id)
