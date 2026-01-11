"""Trip Count Station tool for Windmill.

Calculates public transport trip counts per station within a time window.
"""

import logging
import os
from pathlib import Path
from typing import Any, Self

from pydantic import Field

from goatlib.analysis.accessibility import (
    TripCountStationTool,
    TripCountStationParams as AnalysisTripCountParams,
    PTTimeWindow,
)
from goatlib.analysis.schemas.catchment_area import Weekday
from goatlib.analysis.schemas.ui import (
    UISection,
    ui_field,
    ui_sections,
)
from goatlib.models.io import DatasetMetadata
from goatlib.tools.base import BaseToolRunner
from goatlib.tools.schemas import ScenarioSelectorMixin, ToolInputBase
from goatlib.tools.style import get_trip_count_style

logger = logging.getLogger(__name__)

# Default GTFS data path from environment
GTFS_DATA_PATH = os.environ.get("GTFS_DATA_PATH", "/app/data/gtfs")

# Section definitions for this tool
SECTION_CALCULATION_TIME = UISection(id="calculation_time", order=1, icon="clock")
SECTION_CONFIGURATION = UISection(id="configuration", order=2, icon="settings")


class TripCountToolParams(ScenarioSelectorMixin, ToolInputBase):
    """Parameters for Trip Count Station tool.

    Calculates public transport trip counts per station within a time window,
    grouped by transport mode (bus, tram, metro, rail, other).
    """

    model_config = {
        "json_schema_extra": ui_sections(
            SECTION_CALCULATION_TIME,
            SECTION_CONFIGURATION,
            UISection(
                id="scenario",
                order=8,
                icon="scenario",
                depends_on={"reference_area_layer_id": {"$ne": None}},
            ),
        )
    }

    # Time window section
    weekday: Weekday = Field(
        default=Weekday.weekday,
        description="Type of day for public transport schedule",
        json_schema_extra=ui_field(
            section="calculation_time",
            field_order=1,
            label_key="weekday",
        ),
    )
    from_time: int = Field(
        default=25200,  # 7:00 AM
        description="Start time of the analysis window",
        json_schema_extra=ui_field(
            section="calculation_time",
            field_order=2,
            label_key="from_time",
            widget="time-picker",
        ),
    )
    to_time: int = Field(
        default=32400,  # 9:00 AM
        description="End time of the analysis window",
        json_schema_extra=ui_field(
            section="calculation_time",
            field_order=3,
            label_key="to_time",
            widget="time-picker",
        ),
    )

    # Configuration section
    reference_area_layer_id: str = Field(
        description="Layer ID for the reference area polygon",
        json_schema_extra=ui_field(
            section="configuration",
            field_order=1,
            label_key="reference_area_path",
            widget="layer-selector",
            widget_options={"geometry_types": ["Polygon", "MultiPolygon"]},
        ),
    )
    reference_area_layer_filter: dict[str, Any] | None = Field(
        None,
        description="CQL2-JSON filter to apply to the reference area layer",
        json_schema_extra=ui_field(section="configuration", field_order=2, hidden=True),
    )

    # Hidden internal fields
    reference_area_path: str | None = None  # type: ignore[assignment]
    stops_path: str | None = Field(
        default=None,
        description="Path to GTFS stops parquet file.",
        json_schema_extra=ui_field(section="configuration", hidden=True),
    )
    stop_times_path: str | None = Field(
        default=None,
        description="Path to GTFS stop_times parquet file.",
        json_schema_extra=ui_field(section="configuration", hidden=True),
    )
    output_path: str | None = Field(
        default=None,
        description="Output path for trip count layer.",
        json_schema_extra=ui_field(section="configuration", hidden=True),
    )


class TripCountToolRunner(BaseToolRunner[TripCountToolParams]):
    """Trip Count Station tool runner for Windmill."""

    tool_class = TripCountStationTool
    output_geometry_type = "point"
    default_output_name = "Trip_Count"

    def get_layer_properties(
        self: Self,
        params: TripCountToolParams,
        metadata: DatasetMetadata,
        table_info: dict[str, Any] | None = None,
    ) -> dict[str, Any] | None:
        """Return trip count style with graduated color scale for total trips."""
        color_field = "total"

        # Compute quantile breaks from the DuckLake table (6 breaks for 7 colors)
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

        return get_trip_count_style(color_scale_breaks=color_scale_breaks)

    def process(
        self: Self, params: TripCountToolParams, temp_dir: Path
    ) -> tuple[Path, DatasetMetadata]:
        """Run Trip Count Station analysis."""
        output_path = temp_dir / "output.parquet"

        # Export reference area layer
        reference_area_path = str(
            self.export_layer_to_parquet(
                layer_id=params.reference_area_layer_id,
                user_id=params.user_id,
                cql_filter=params.reference_area_layer_filter,
                scenario_id=params.scenario_id,
                project_id=params.project_id,
            )
        )

        # Use GTFS paths from params or derive from GTFS_DATA_PATH environment variable
        stops_path = params.stops_path or f"{GTFS_DATA_PATH}/stops.parquet"
        stop_times_path = (
            params.stop_times_path or f"{GTFS_DATA_PATH}/stop_times_optimized.parquet"
        )

        # Build time window (weekday is StrEnum, use .value)
        time_window = PTTimeWindow(
            weekday=params.weekday.value
            if hasattr(params.weekday, "value")
            else params.weekday,
            from_time=params.from_time,
            to_time=params.to_time,
        )

        # Build params for the analysis tool
        analysis_params = AnalysisTripCountParams(
            reference_area_path=reference_area_path,
            stops_path=stops_path,
            stop_times_path=stop_times_path,
            time_window=time_window,
            output_path=str(output_path),
        )

        tool = self.tool_class()
        stats = tool.run(analysis_params)
        logger.info("TripCount stats: %s", stats)

        # Create metadata for the output parquet
        metadata = DatasetMetadata(
            path=str(output_path),
            source_type="vector",
            geometry_type="Point",
            crs="EPSG:4326",
        )
        return output_path, metadata


def main(params: TripCountToolParams) -> dict:
    """Windmill entry point for Trip Count Station tool."""
    runner = TripCountToolRunner()
    runner.init_from_env()

    try:
        return runner.run(params)
    finally:
        runner.cleanup()
