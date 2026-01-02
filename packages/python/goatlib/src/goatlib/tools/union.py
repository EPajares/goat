"""Union tool for Windmill.

Computes the geometric union of features from input and overlay layers.
"""

import logging
from pathlib import Path
from typing import Self

from goatlib.analysis.geoprocessing.union import UnionTool
from goatlib.analysis.schemas.geoprocessing import UnionParams
from goatlib.models.io import DatasetMetadata
from goatlib.tools.base import BaseToolRunner
from goatlib.tools.schemas import ToolInputBase, TwoLayerInputMixin

logger = logging.getLogger(__name__)


class UnionToolParams(ToolInputBase, TwoLayerInputMixin, UnionParams):
    """Parameters for union tool.

    Inherits union options from UnionParams, adds layer context from ToolInputBase.
    input_path/overlay_path/output_path are not used (we use layer IDs instead).
    """

    input_path: str | None = None  # type: ignore[assignment]
    overlay_path: str | None = None  # type: ignore[assignment]
    output_path: str | None = None


class UnionToolRunner(BaseToolRunner[UnionToolParams]):
    """Union tool runner for Windmill."""

    tool_class = UnionTool
    output_geometry_type = None  # Depends on input
    default_output_name = "Union"

    def process(
        self: Self, params: UnionToolParams, temp_dir: Path
    ) -> tuple[Path, DatasetMetadata]:
        """Run union analysis."""
        input_path = self.export_layer_to_parquet(params.input_layer_id, params.user_id)
        overlay_path = self.export_layer_to_parquet(
            params.overlay_layer_id, params.user_id
        )
        output_path = temp_dir / "output.parquet"

        analysis_params = UnionParams(
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


def main(params: UnionToolParams) -> dict:
    """Windmill entry point for union tool."""
    runner = UnionToolRunner()
    runner.init_from_env()

    try:
        return runner.run(params)
    finally:
        runner.cleanup()
