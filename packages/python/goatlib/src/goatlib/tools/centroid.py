"""Centroid tool for Windmill.

Computes the centroid of each feature in the input layer.
"""

import logging
from pathlib import Path
from typing import Self

from goatlib.analysis.geoprocessing.centroid import CentroidTool
from goatlib.analysis.schemas.geoprocessing import CentroidParams
from goatlib.models.io import DatasetMetadata
from goatlib.tools.base import BaseToolRunner
from goatlib.tools.schemas import LayerInputMixin, ToolInputBase

logger = logging.getLogger(__name__)


class CentroidToolParams(ToolInputBase, LayerInputMixin, CentroidParams):
    """Parameters for centroid tool.

    Inherits centroid options from CentroidParams, adds layer context from ToolInputBase.
    input_path/output_path are not used (we use layer IDs instead).
    """

    input_path: str | None = None  # type: ignore[assignment]
    output_path: str | None = None


class CentroidToolRunner(BaseToolRunner[CentroidToolParams]):
    """Centroid tool runner for Windmill."""

    tool_class = CentroidTool
    output_geometry_type = "Point"
    default_output_name = "Centroid"

    def process(
        self: Self, params: CentroidToolParams, temp_dir: Path
    ) -> tuple[Path, DatasetMetadata]:
        """Run centroid analysis."""
        input_path = self.export_layer_to_parquet(params.input_layer_id, params.user_id)
        output_path = temp_dir / "output.parquet"

        analysis_params = CentroidParams(
            **params.model_dump(
                exclude={
                    "input_path",
                    "output_path",
                    "user_id",
                    "folder_id",
                    "project_id",
                    "output_name",
                    "input_layer_id",
                }
            ),
            input_path=input_path,
            output_path=str(output_path),
        )

        tool = self.tool_class()
        try:
            results = tool.run(analysis_params)
            result_path, metadata = results[0]
            return Path(result_path), metadata
        finally:
            tool.cleanup()


def main(params: CentroidToolParams) -> dict:
    """Windmill entry point for centroid tool."""
    runner = CentroidToolRunner()
    runner.init_from_env()

    try:
        return runner.run(params)
    finally:
        runner.cleanup()
