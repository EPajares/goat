"""Origin-Destination tool for Windmill.

Creates origin-destination lines and points from a geometry layer and OD matrix.
"""

import logging
from pathlib import Path
from typing import Self

from goatlib.analysis.geoprocessing.origin_destination import OriginDestinationTool
from goatlib.analysis.schemas.geoprocessing import OriginDestinationParams
from goatlib.models.io import DatasetMetadata
from goatlib.tools.base import BaseToolRunner
from goatlib.tools.schemas import ToolInputBase

logger = logging.getLogger(__name__)


class OriginDestinationToolParams(ToolInputBase, OriginDestinationParams):
    """Parameters for origin-destination tool.

    Inherits OD options from OriginDestinationParams, adds layer context from ToolInputBase.
    geometry_path/matrix_path/output_paths are not used (we use layer IDs instead).
    """

    geometry_path: str | None = None  # type: ignore[assignment]
    matrix_path: str | None = None  # type: ignore[assignment]
    output_path_lines: str | None = None
    output_path_points: str | None = None

    # Layer ID for the geometry (origins/destinations)
    geometry_layer_id: str


class OriginDestinationToolRunner(BaseToolRunner[OriginDestinationToolParams]):
    """Origin-Destination tool runner for Windmill."""

    tool_class = OriginDestinationTool
    output_geometry_type = "LineString"  # Primary output
    default_output_name = "OD_Lines"

    def process(
        self: Self, params: OriginDestinationToolParams, temp_dir: Path
    ) -> tuple[Path, DatasetMetadata]:
        """Run origin-destination analysis."""
        # Export geometry layer
        geometry_path = self.export_layer_to_parquet(
            params.geometry_layer_id, params.user_id
        )

        # For the matrix, we need to handle it as a separate file input
        # This would typically come from another layer or uploaded file
        # For now, we'll export from a layer ID if provided
        matrix_path = self.export_layer_to_parquet(
            params.geometry_layer_id, params.user_id, suffix="_matrix"
        )

        output_path_lines = temp_dir / "output_lines.parquet"
        output_path_points = temp_dir / "output_points.parquet"

        analysis_params = OriginDestinationParams(
            **params.model_dump(
                exclude={
                    "geometry_path",
                    "matrix_path",
                    "output_path_lines",
                    "output_path_points",
                    "user_id",
                    "folder_id",
                    "project_id",
                    "output_name",
                    "geometry_layer_id",
                }
            ),
            geometry_path=str(geometry_path),
            matrix_path=str(matrix_path),
            output_path_lines=str(output_path_lines),
            output_path_points=str(output_path_points),
        )

        tool = self.tool_class()
        try:
            results = tool.run(analysis_params)
            # Returns two outputs: lines and points
            # We'll return lines as primary, points can be handled separately
            result_path, metadata = results[0]
            return Path(result_path), metadata
        finally:
            tool.cleanup()


def main(params: OriginDestinationToolParams) -> dict:
    """Windmill entry point for origin-destination tool."""
    runner = OriginDestinationToolRunner()
    runner.init_from_env()

    try:
        return runner.run(params)
    finally:
        runner.cleanup()
