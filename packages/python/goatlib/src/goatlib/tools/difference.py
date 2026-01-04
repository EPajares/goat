"""Difference tool for Windmill.

Computes the geometric difference of features from input and overlay layers.
"""

import logging
from pathlib import Path
from typing import Self

from goatlib.analysis.geoprocessing.difference import DifferenceTool
from goatlib.analysis.schemas.geoprocessing import DifferenceParams
from goatlib.models.io import DatasetMetadata
from goatlib.tools.base import BaseToolRunner
from goatlib.tools.schemas import ToolInputBase, TwoLayerInputMixin

logger = logging.getLogger(__name__)


class DifferenceToolParams(ToolInputBase, TwoLayerInputMixin, DifferenceParams):
    """Parameters for difference tool.

    Inherits difference options from DifferenceParams, adds layer context from ToolInputBase.
    input_path/overlay_path/output_path are not used (we use layer IDs instead).
    """

    input_path: str | None = None  # type: ignore[assignment]
    overlay_path: str | None = None  # type: ignore[assignment]
    output_path: str | None = None


class DifferenceToolRunner(BaseToolRunner[DifferenceToolParams]):
    """Difference tool runner for Windmill."""

    tool_class = DifferenceTool
    output_geometry_type = None  # Depends on input
    default_output_name = "Difference"

    def process(
        self: Self, params: DifferenceToolParams, temp_dir: Path
    ) -> tuple[Path, DatasetMetadata]:
        """Run difference analysis."""
        input_path = self.export_layer_to_parquet(params.input_layer_id, params.user_id)
        overlay_path = self.export_layer_to_parquet(
            params.overlay_layer_id, params.user_id
        )
        output_path = temp_dir / "output.parquet"

        analysis_params = DifferenceParams(
            **params.model_dump(
                exclude={
                    "input_path",
                    "overlay_path",
                    "output_path",
                    "user_id",
                    "folder_id",
                    "project_id",
                    "output_name",
                    "input_layer_id",
                    "overlay_layer_id",
                }
            ),
            input_path=input_path,
            overlay_path=overlay_path,
            output_path=str(output_path),
        )

        tool = self.tool_class()
        try:
            results = tool.run(analysis_params)
            result_path, metadata = results[0]
            return Path(result_path), metadata
        finally:
            tool.cleanup()


def main(params: DifferenceToolParams) -> dict:
    """Windmill entry point for difference tool."""
    runner = DifferenceToolRunner()
    runner.init_from_env()

    try:
        return runner.run(params)
    finally:
        runner.cleanup()
