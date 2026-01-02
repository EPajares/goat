"""Intersection tool for Windmill.

Computes the geometric intersection of features from input and overlay layers.
"""

import logging
from pathlib import Path
from typing import Self

from goatlib.analysis.geoprocessing.intersection import IntersectionTool
from goatlib.analysis.schemas.geoprocessing import IntersectionParams
from goatlib.models.io import DatasetMetadata
from goatlib.tools.base import BaseToolRunner
from goatlib.tools.schemas import ToolInputBase, TwoLayerInputMixin

logger = logging.getLogger(__name__)


class IntersectionToolParams(ToolInputBase, TwoLayerInputMixin, IntersectionParams):
    """Parameters for intersection tool.

    Inherits intersection options from IntersectionParams, adds layer context from ToolInputBase.
    input_path/overlay_path/output_path are not used (we use layer IDs instead).
    """

    input_path: str | None = None  # type: ignore[assignment]
    overlay_path: str | None = None  # type: ignore[assignment]
    output_path: str | None = None


class IntersectionToolRunner(BaseToolRunner[IntersectionToolParams]):
    """Intersection tool runner for Windmill."""

    tool_class = IntersectionTool
    output_geometry_type = None  # Depends on input
    default_output_name = "Intersection"

    def process(
        self: Self, params: IntersectionToolParams, temp_dir: Path
    ) -> tuple[Path, DatasetMetadata]:
        """Run intersection analysis."""
        input_path = self.export_layer_to_parquet(params.input_layer_id, params.user_id)
        overlay_path = self.export_layer_to_parquet(
            params.overlay_layer_id, params.user_id
        )
        output_path = temp_dir / "output.parquet"

        analysis_params = IntersectionParams(
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


def main(params: IntersectionToolParams) -> dict:
    """Windmill entry point for intersection tool."""
    runner = IntersectionToolRunner()
    runner.init_from_env()

    try:
        return runner.run(params)
    finally:
        runner.cleanup()
