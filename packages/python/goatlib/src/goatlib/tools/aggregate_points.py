"""Aggregate Points tool for Windmill.

Aggregates point features onto polygons or H3 hexagonal grids,
computing statistics like count, sum, mean, min, or max.
"""

import logging
from pathlib import Path
from typing import Any, Optional, Self

from pydantic import Field, model_validator

from goatlib.analysis.geoanalysis.aggregate_points import AggregatePointsTool
from goatlib.analysis.schemas.aggregate import (
    AggregatePointsParams,
    AggregationAreaType,
    ColumnStatistic,
    validate_area_type_config,
)
from goatlib.analysis.schemas.ui import (
    SECTION_AREA,
    SECTION_INPUT_AGGREGATE,
    SECTION_STATISTICS,
    ui_field,
    ui_sections,
)
from goatlib.models.io import DatasetMetadata
from goatlib.tools.base import BaseToolRunner
from goatlib.tools.schemas import ToolInputBase

logger = logging.getLogger(__name__)


class AggregatePointsToolParams(ToolInputBase, AggregatePointsParams):
    """Parameters for aggregate points tool.

    Inherits aggregate options from AggregatePointsParams, adds layer context from ToolInputBase.
    source_path/area_layer_path/output_path are not used (we use layer IDs instead).
    """

    model_config = {
        "json_schema_extra": ui_sections(
            SECTION_INPUT_AGGREGATE,
            SECTION_AREA,
            SECTION_STATISTICS,
        )
    }

    # Override file paths as optional - we use layer IDs instead
    source_path: str | None = Field(
        None,
        description="Path to the point layer (auto-populated from source_layer_id).",
        json_schema_extra=ui_field(section="input", hidden=True),
    )
    area_layer_path: str | None = Field(
        None,
        description="Path to the area layer (auto-populated from area_layer_id).",
        json_schema_extra=ui_field(section="area", hidden=True),
    )
    output_path: str | None = Field(
        None,
        description="Output path (auto-generated).",
        json_schema_extra=ui_field(section="output", hidden=True),
    )

    # ---- Layer ID fields (UI uses these instead of paths) ----
    source_layer_id: str = Field(
        ...,
        description="Layer ID for the point layer to be aggregated.",
        json_schema_extra=ui_field(
            section="input",
            field_order=1,
            label_key="select_source_layer",
            widget="layer-selector",
            widget_options={"geometry_types": ["Point", "MultiPoint"]},
        ),
    )

    area_layer_id: Optional[str] = Field(
        None,
        description="Layer ID for the polygon layer used for aggregation. Required when area_type is 'polygon'.",
        json_schema_extra=ui_field(
            section="area",
            field_order=2,
            label_key="select_area_layer",
            widget="layer-selector",
            widget_options={"geometry_types": ["Polygon", "MultiPolygon"]},
            visible_when={"area_type": "polygon"},
        ),
    )

    # Override UI metadata for inherited fields
    area_type: AggregationAreaType = Field(
        ...,
        description="Type of area to aggregate points into: polygon layer or H3 hexagonal grid.",
        json_schema_extra=ui_field(
            section="area",
            field_order=1,
            label_key="select_area_type",
        ),
    )

    column_statistics: ColumnStatistic = Field(
        ...,
        description="Statistical operation to perform on the aggregated points.",
        json_schema_extra=ui_field(
            section="statistics",
            field_order=1,
            label_key="select_statistics_configuration",
        ),
    )

    @model_validator(mode="after")
    def validate_area_configuration(self: Self) -> "AggregatePointsToolParams":
        """Override parent validator to check area_layer_id instead of area_layer_path."""
        validate_area_type_config(
            area_type=self.area_type,
            area_layer=self.area_layer_id,
            h3_resolution=self.h3_resolution,
            area_layer_field_name="area_layer_id",
        )
        return self


class AggregatePointsToolRunner(BaseToolRunner[AggregatePointsToolParams]):
    """Aggregate Points tool runner for Windmill."""

    tool_class = AggregatePointsTool
    output_geometry_type = "polygon"
    default_output_name = "Aggregated_Points"

    def get_layer_properties(
        self: Self,
        params: AggregatePointsToolParams,
        metadata: DatasetMetadata,
        table_info: dict[str, Any] | None = None,
    ) -> dict[str, Any] | None:
        """Return style for aggregated output with quantile breaks."""
        # Determine the value field based on the statistics operation
        stat_op = params.column_statistics.operation
        stat_field = params.column_statistics.field

        if stat_op.value == "count":
            color_field = "count"
        else:
            # For sum/mean/min/max, the output column is named after the operation
            color_field = (
                f"{stat_op.value}_{stat_field}" if stat_field else stat_op.value
            )

        # Compute quantile breaks from the DuckLake table
        color_scale_breaks = None
        if table_info and table_info.get("table_name"):
            color_scale_breaks = self.compute_quantile_breaks(
                table_name=table_info["table_name"],
                column_name=color_field,
                num_breaks=6,
                strip_zeros=True,
            )
            if color_scale_breaks:
                logger.info(
                    "Computed quantile breaks for %s: %s",
                    color_field,
                    color_scale_breaks,
                )

        # Import here to avoid circular imports
        from goatlib.tools.style import get_heatmap_style

        # Use Orange for aggregation - represents count/sum data
        return get_heatmap_style(
            color_field_name=color_field,
            color_scale_breaks=color_scale_breaks,
            color_range_name="Oranges",
        )

    def process(
        self: Self, params: AggregatePointsToolParams, temp_dir: Path
    ) -> tuple[Path, DatasetMetadata]:
        """Run aggregate points analysis."""
        output_path = temp_dir / "output.parquet"

        # Export source point layer
        source_path = str(
            self.export_layer_to_parquet(params.source_layer_id, params.user_id)
        )

        # Export area layer if polygon aggregation
        area_layer_path = None
        if params.area_type == AggregationAreaType.polygon and params.area_layer_id:
            area_layer_path = str(
                self.export_layer_to_parquet(params.area_layer_id, params.user_id)
            )

        # Build analysis params using model_dump pattern (like other tools)
        analysis_params = AggregatePointsParams(
            **params.model_dump(
                exclude={
                    "source_path",
                    "area_layer_path",
                    "output_path",
                    "output_crs",
                    "user_id",
                    "folder_id",
                    "project_id",
                    "output_name",
                    "source_layer_id",
                    "area_layer_id",
                    "accepted_source_geometry_types",
                    "accepted_area_geometry_types",
                }
            ),
            source_path=source_path,
            area_layer_path=area_layer_path,
            output_path=str(output_path),
        )

        tool = self.tool_class()
        try:
            results = tool.run(analysis_params)
            result_path, metadata = results[0]
            return Path(result_path), metadata
        finally:
            tool.cleanup()


def main(params: AggregatePointsToolParams) -> dict:
    """Windmill entry point for aggregate points tool.

    This function is called by Windmill with parameters from the job.
    Environment variables provide database connection settings.

    Args:
        params: Parameters matching AggregatePointsToolParams schema

    Returns:
        Dict with output layer metadata
    """
    runner = AggregatePointsToolRunner()
    runner.init_from_env()

    try:
        return runner.run(params)
    finally:
        runner.cleanup()
