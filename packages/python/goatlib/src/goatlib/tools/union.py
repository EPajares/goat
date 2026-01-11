"""Union tool for Windmill.

Computes the geometric union of features from input and overlay layers.
Supports self-union when no overlay layer is provided.
"""

import logging
from pathlib import Path
from typing import Any, Optional, Self

from pydantic import ConfigDict, Field

from goatlib.analysis.geoprocessing.union import UnionTool
from goatlib.analysis.schemas.geoprocessing import UnionParams
from goatlib.analysis.schemas.ui import (
    SECTION_INPUT,
    SECTION_OUTPUT,
    UISection,
    ui_field,
    ui_sections,
)
from goatlib.models.io import DatasetMetadata
from goatlib.tools.base import BaseToolRunner
from goatlib.tools.schemas import LayerInputMixin, ScenarioSelectorMixin, ToolInputBase

logger = logging.getLogger(__name__)


class UnionToolParams(
    ScenarioSelectorMixin, ToolInputBase, LayerInputMixin, UnionParams
):
    """Parameters for union tool.

    Inherits union options from UnionParams, adds layer context from ToolInputBase.
    input_path/overlay_path/output_path are not used (we use layer IDs instead).
    Overlay layer is optional - if not provided, performs self-union on input.
    """

    model_config = ConfigDict(
        json_schema_extra=ui_sections(
            SECTION_INPUT,
            UISection(id="overlay", order=2, icon="layers"),
            UISection(
                id="scenario",
                order=8,
                icon="scenario",
                collapsible=True,
                collapsed=True,
                depends_on={"input_layer_id": {"$ne": None}},
            ),
            SECTION_OUTPUT,
        )
    )

    input_path: str | None = None  # type: ignore[assignment]
    overlay_path: str | None = None  # type: ignore[assignment]
    output_path: str | None = None

    # Override overlay_layer_id to make it optional for self-union
    overlay_layer_id: Optional[str] = Field(
        None,
        description="Overlay layer UUID. If not provided, performs self-union on input layer.",
        json_schema_extra=ui_field(
            section="overlay",
            field_order=1,
            widget="layer-selector",
        ),
    )
    overlay_layer_filter: dict[str, Any] | None = Field(
        None,
        description="CQL2-JSON filter to apply to the overlay layer",
        json_schema_extra=ui_field(section="overlay", field_order=2, hidden=True),
    )

    # Override to reference overlay_layer_id instead of overlay_path
    overlay_fields_prefix: Optional[str] = Field(
        None,
        description="Prefix to add to overlay field names to avoid naming conflicts.",
        json_schema_extra=ui_field(
            section="overlay",
            field_order=3,
            visible_when={"overlay_layer_id": {"$ne": None}},
        ),
    )


class UnionToolRunner(BaseToolRunner[UnionToolParams]):
    """Union tool runner for Windmill."""

    tool_class = UnionTool
    output_geometry_type = None  # Depends on input
    default_output_name = "Union"

    def process(
        self: Self, params: UnionToolParams, temp_dir: Path
    ) -> tuple[Path, DatasetMetadata]:
        """Run union analysis."""
        input_path = self.export_layer_to_parquet(
            layer_id=params.input_layer_id,
            user_id=params.user_id,
            cql_filter=params.input_layer_filter,
            scenario_id=params.scenario_id,
            project_id=params.project_id,
        )

        # Overlay is optional - if not provided, performs self-union
        overlay_path = None
        if params.overlay_layer_id:
            overlay_path = self.export_layer_to_parquet(
                layer_id=params.overlay_layer_id,
                user_id=params.user_id,
                cql_filter=params.overlay_layer_filter,
                scenario_id=params.scenario_id,
                project_id=params.project_id,
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


def main(params: UnionToolParams) -> dict:
    """Windmill entry point for union tool."""
    runner = UnionToolRunner()
    runner.init_from_env()

    try:
        return runner.run(params)
    finally:
        runner.cleanup()
