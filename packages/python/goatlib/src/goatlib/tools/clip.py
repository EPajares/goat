"""Clip tool for Windmill.

Clips features from an input layer using overlay layer geometry.
"""

import logging
from pathlib import Path
from typing import Self

from goatlib.analysis.geoprocessing.clip import ClipTool
from goatlib.analysis.schemas.geoprocessing import ClipParams
from goatlib.models.io import DatasetMetadata
from goatlib.tools.base import BaseToolRunner
from goatlib.tools.schemas import ToolInputBase, TwoLayerInputMixin

logger = logging.getLogger(__name__)


class ClipToolParams(ToolInputBase, TwoLayerInputMixin, ClipParams):
    """Parameters for clip tool.

    Inherits clip options from ClipParams, adds layer context from ToolInputBase.
    input_path/overlay_path/output_path are not used (we use layer IDs instead).
    """

    input_path: str | None = None  # type: ignore[assignment]
    overlay_path: str | None = None  # type: ignore[assignment]
    output_path: str | None = None


class ClipToolRunner(BaseToolRunner[ClipToolParams]):
    """Clip tool runner for Windmill."""

    tool_class = ClipTool
    output_geometry_type = None  # Preserves input geometry type
    default_output_name = "Clip"

    def process(
        self: Self, params: ClipToolParams, temp_dir: Path
    ) -> tuple[Path, DatasetMetadata]:
        """Run clip analysis."""
        input_path = self.export_layer_to_parquet(
            layer_id=params.input_layer_id,
            user_id=params.user_id,
            cql_filter=params.input_layer_filter,
            scenario_id=params.scenario_id,
            project_id=params.project_id,
        )
        overlay_path = self.export_layer_to_parquet(
            layer_id=params.overlay_layer_id,
            user_id=params.user_id,
            cql_filter=params.overlay_layer_filter,
            scenario_id=params.scenario_id,
            project_id=params.project_id,
        )
        output_path = temp_dir / "output.parquet"

        analysis_params = ClipParams(
            **params.model_dump(
                exclude={
                    "input_path",
                    "overlay_path",
                    "output_path",
                    "user_id",
                    "folder_id",
                    "project_id",
                    "scenario_id",
                    "output_name",
                    "input_layer_id",
                    "input_layer_filter",
                    "overlay_layer_id",
                    "overlay_layer_filter",
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


def main(params: ClipToolParams) -> dict:
    """Windmill entry point for clip tool."""
    runner = ClipToolRunner()
    runner.init_from_env()

    try:
        return runner.run(params)
    finally:
        runner.cleanup()
