"""ÖV-Güteklassen (Public Transport Quality Classes) tool for Windmill.

Calculates public transport quality classes based on the Swiss ARE methodology.
"""

import logging
import os
from enum import StrEnum
from pathlib import Path
from typing import Any, Self

from pydantic import Field

from goatlib.analysis.accessibility import (
    STATION_CONFIG_DEFAULT,
    OevGueteklasseTool,
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
from goatlib.tools.schemas import ToolInputBase
from goatlib.tools.style import (
    get_oev_gueteklassen_stations_style,
    get_oev_gueteklassen_style,
)

logger = logging.getLogger(__name__)

# Default GTFS data path from environment
GTFS_DATA_PATH = os.environ.get("GTFS_DATA_PATH", "/app/data/gtfs")

# Section definitions for this tool (no depends_on conditions)
SECTION_CALCULATION_TIME = UISection(id="calculation_time", order=1, icon="clock")
SECTION_OEV_CONFIGURATION = UISection(id="configuration", order=2, icon="settings")


class CatchmentType(StrEnum):
    """Catchment area type for ÖV-Güteklassen."""

    buffer = "buffer"


class OevGueteklassenToolParams(ToolInputBase):
    """Parameters for ÖV-Güteklassen tool.

    Calculates public transport quality classes based on station accessibility
    and service frequency.
    """

    model_config = {
        "json_schema_extra": ui_sections(
            SECTION_CALCULATION_TIME,
            SECTION_OEV_CONFIGURATION,
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
    catchment_type: CatchmentType = Field(
        default=CatchmentType.buffer,
        description="Method for calculating catchment areas",
        json_schema_extra=ui_field(
            section="configuration",
            field_order=1,
            label_key="catchment_type",
        ),
    )
    reference_area_layer_id: str = Field(
        description="Layer ID for the reference area polygon",
        json_schema_extra=ui_field(
            section="configuration",
            field_order=2,
            label_key="reference_area_path",
            widget="layer-selector",
            widget_options={"geometry_types": ["Polygon", "MultiPolygon"]},
        ),
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
        description="Output path for quality classes layer.",
        json_schema_extra=ui_field(section="configuration", hidden=True),
    )


class OevGueteklassenToolRunner(BaseToolRunner[OevGueteklassenToolParams]):
    """ÖV-Güteklassen tool runner for Windmill."""

    tool_class = OevGueteklasseTool
    output_geometry_type = "polygon"
    default_output_name = "OeV_Gueteklassen"

    # Store stations output path for secondary layer creation
    _stations_parquet: Path | None = None

    def get_layer_properties(
        self: Self,
        params: OevGueteklassenToolParams,
        metadata: DatasetMetadata,
        table_info: dict[str, Any] | None = None,
    ) -> dict[str, Any] | None:
        """Return ÖV-Güteklassen style with ordinal color scale for A-F classes."""
        return get_oev_gueteklassen_style()

    def process(
        self: Self, params: OevGueteklassenToolParams, temp_dir: Path
    ) -> tuple[Path, DatasetMetadata]:
        """Run ÖV-Güteklassen analysis."""
        output_path = temp_dir / "output.parquet"
        stations_output_path = temp_dir / "stations.parquet"

        # Export reference area layer
        reference_area_path = str(
            self.export_layer_to_parquet(params.reference_area_layer_id, params.user_id)
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

        tool = self.tool_class()
        try:
            stats = tool.run(
                reference_area_path=reference_area_path,
                stops_path=stops_path,
                stop_times_path=stop_times_path,
                time_window=time_window,
                output_path=str(output_path),
                station_config=STATION_CONFIG_DEFAULT,
                stations_output_path=str(stations_output_path),
            )
            logger.info("OevGueteklassen stats: %s", stats)

            # Store stations path for secondary layer creation
            if stations_output_path.exists():
                self._stations_parquet = stations_output_path
                logger.info("Stations output available at: %s", stations_output_path)

            # Create metadata for the output parquet
            metadata = DatasetMetadata(
                path=str(output_path),
                source_type="vector",
                geometry_type="Polygon",
                crs="EPSG:4326",
            )
            return output_path, metadata
        finally:
            tool.cleanup()

    def run(self: Self, params: OevGueteklassenToolParams) -> dict:
        """Run tool and create both polygon and station layers."""
        import asyncio
        import tempfile
        import uuid as uuid_module

        from goatlib.tools.schemas import ToolOutputBase

        # Main polygon layer
        output_layer_id = str(uuid_module.uuid4())
        output_name = params.output_name or self.default_output_name

        # Stations layer
        stations_layer_id = str(uuid_module.uuid4())
        stations_output_name = f"{output_name}_Stations"

        logger.info(
            f"Starting tool: {self.__class__.__name__} "
            f"(user={params.user_id}, output={output_layer_id})"
        )

        # Initialize db_service
        asyncio.get_event_loop().run_until_complete(self._init_db_service())

        with tempfile.TemporaryDirectory(
            prefix=f"{self.__class__.__name__.lower()}_"
        ) as temp_dir:
            temp_path = Path(temp_dir)

            # Step 1: Run analysis (creates both polygon and stations outputs)
            output_parquet, metadata = self.process(params, temp_path)
            logger.info(
                f"Analysis complete: {metadata.feature_count or 0} features "
                f"at {output_parquet}"
            )

            # Step 2: Ingest polygon layer to DuckLake
            table_info = self._ingest_to_ducklake(
                user_id=params.user_id,
                layer_id=output_layer_id,
                parquet_path=output_parquet,
            )
            logger.info(f"DuckLake polygon table created: {table_info['table_name']}")

            # Step 2b: Ingest stations layer to DuckLake (if available)
            stations_table_info = None
            if self._stations_parquet and self._stations_parquet.exists():
                stations_table_info = self._ingest_to_ducklake(
                    user_id=params.user_id,
                    layer_id=stations_layer_id,
                    parquet_path=self._stations_parquet,
                )
                logger.info(
                    f"DuckLake stations table created: {stations_table_info['table_name']}"
                )

            # Refresh database pool
            asyncio.get_event_loop().run_until_complete(self._close_db_service())

            # Step 3: Create polygon layer DB records
            result_info = asyncio.get_event_loop().run_until_complete(
                self._create_db_records(
                    output_layer_id=output_layer_id,
                    params=params,
                    output_name=output_name,
                    metadata=metadata,
                    table_info=table_info,
                )
            )

            # Step 3b: Create stations layer DB records (if available)
            stations_result_info = None
            if stations_table_info:
                stations_metadata = DatasetMetadata(
                    path=str(self._stations_parquet),
                    source_type="vector",
                    geometry_type="Point",
                    crs="EPSG:4326",
                )
                stations_result_info = asyncio.get_event_loop().run_until_complete(
                    self._create_db_records(
                        output_layer_id=stations_layer_id,
                        params=params,
                        output_name=stations_output_name,
                        metadata=stations_metadata,
                        table_info=stations_table_info,
                        custom_properties=get_oev_gueteklassen_stations_style(),
                    )
                )
                logger.info(f"Stations layer created: {stations_layer_id}")

        # Close database pool
        asyncio.get_event_loop().run_until_complete(self._close_db_service())

        # Build main output
        detected_geom_type = table_info.get("geometry_type")
        is_feature = bool(detected_geom_type)
        output = ToolOutputBase(
            layer_id=output_layer_id,
            name=output_name,
            folder_id=result_info["folder_id"],
            user_id=params.user_id,
            project_id=params.project_id,
            layer_project_id=result_info.get("layer_project_id"),
            type="feature" if is_feature else "table",
            feature_layer_type=self.get_feature_layer_type(params)
            if is_feature
            else None,
            geometry_type=detected_geom_type,
            feature_count=table_info.get("feature_count", 0),
            extent=table_info.get("extent"),
            table_name=table_info["table_name"],
        )

        result = output.model_dump()

        # Add stations layer info if created
        if stations_table_info and stations_result_info:
            result["stations_layer"] = {
                "layer_id": stations_layer_id,
                "name": stations_output_name,
                "folder_id": stations_result_info["folder_id"],
                "layer_project_id": stations_result_info.get("layer_project_id"),
                "geometry_type": stations_table_info.get("geometry_type"),
                "feature_count": stations_table_info.get("feature_count", 0),
                "table_name": stations_table_info["table_name"],
            }

        logger.info(f"Tool completed: {output_layer_id} ({output_name})")
        return result


def main(params: OevGueteklassenToolParams) -> dict:
    """Windmill entry point for ÖV-Güteklassen tool."""
    runner = OevGueteklassenToolRunner()
    runner.init_from_env()

    try:
        return runner.run(params)
    finally:
        runner.cleanup()
