"""Catchment Area tool for Windmill.

Computes catchment areas (isochrones) for various transport modes via routing services.
"""

import logging
from pathlib import Path
from typing import Any, Self

from pydantic import Field

from goatlib.analysis.accessibility import CatchmentAreaTool
from goatlib.analysis.schemas.catchment_area import (
    CATCHMENT_AREA_TYPE_LABELS,
    MEASURE_TYPE_ICONS,
    MEASURE_TYPE_LABELS,
    PT_MODE_ICONS,
    PT_MODE_LABELS,
    ROUTING_MODE_ICONS,
    ROUTING_MODE_LABELS,
    SPEED_LABELS,
    TRAVEL_TIME_LABELS,
    AccessEgressMode,
    CatchmentAreaMeasureType,
    CatchmentAreaRoutingMode,
    CatchmentAreaSteps,
    CatchmentAreaToolParams,
    CatchmentAreaType,
    PTMode,
    PTTimeWindow,
    SpeedKmh,
    StartingPoints,
    StartingPointsLayer,
    StartingPointsMap,
    TravelTimeLimitActiveMobility,
    TravelTimeLimitMotorized,
    Weekday,
)
from goatlib.analysis.schemas.ui import (
    SECTION_ROUTING,
    UISection,
    ui_field,
    ui_sections,
)
from goatlib.models.io import DatasetMetadata
from goatlib.tools.base import BaseToolRunner
from goatlib.tools.schemas import ToolInputBase

logger = logging.getLogger(__name__)

# Custom sections for catchment area UI
# Order: routing (1), configuration (2), starting_points (3), scenario (4)
SECTION_CONFIGURATION = UISection(
    id="configuration",
    order=2,
    icon="settings",
    label_key="configuration",
    depends_on={"routing_mode": {"$ne": None}},
)

SECTION_STARTING = UISection(
    id="starting",
    order=3,
    icon="location",
    label_key="starting_points",
    depends_on={"routing_mode": {"$ne": None}},
)

SECTION_SCENARIO = UISection(
    id="scenario",
    order=4,
    icon="git-branch",  # scenario/branch icon for network modifications
    label_key="scenario",
    depends_on={"routing_mode": {"$ne": None}},
)


class CatchmentAreaWindmillParams(ToolInputBase):
    """Parameters for catchment area tool via Windmill/GeoAPI.

    This schema extends ToolInputBase with catchment area specific parameters.
    The frontend renders this dynamically based on x-ui metadata.
    """

    model_config = {
        "json_schema_extra": ui_sections(
            SECTION_ROUTING,
            SECTION_CONFIGURATION,
            SECTION_STARTING,
            SECTION_SCENARIO,
        )
    }

    # =========================================================================
    # Routing Section
    # =========================================================================
    routing_mode: CatchmentAreaRoutingMode = Field(
        ...,
        description="Transport mode for the catchment area calculation.",
        json_schema_extra=ui_field(
            section="routing",
            field_order=1,
            enum_icons=ROUTING_MODE_ICONS,
            enum_labels=ROUTING_MODE_LABELS,
        ),
    )

    pt_modes: list[PTMode] | None = Field(
        default=list(PTMode),
        description="Public transport modes to include.",
        json_schema_extra=ui_field(
            section="routing",
            field_order=2,
            label_key="routing_pt_mode",
            description_key="choose_pt_mode",
            enum_icons=PT_MODE_ICONS,
            enum_labels=PT_MODE_LABELS,
            visible_when={"routing_mode": "pt"},
        ),
    )

    # =========================================================================
    # Starting Points Section
    # =========================================================================
    starting_points: StartingPoints = Field(
        ...,
        description="Starting point(s) for the catchment area - either map coordinates or a layer.",
        json_schema_extra=ui_field(
            section="starting",
            field_order=1,
            widget="starting-points",
            widget_options={"geometry_types": ["Point", "MultiPoint"]},
        ),
    )

    # =========================================================================
    # Configuration Section
    # =========================================================================
    measure_type: CatchmentAreaMeasureType = Field(
        default=CatchmentAreaMeasureType.time,
        description="Measure catchment area by travel time or distance.",
        json_schema_extra=ui_field(
            section="configuration",
            field_order=1,
            label_key="measure_type",
            enum_labels=MEASURE_TYPE_LABELS,
            enum_icons=MEASURE_TYPE_ICONS,
            visible_when={
                "routing_mode": {"$in": ["walking", "bicycle", "pedelec", "car"]}
            },
        ),
    )

    # Travel time for active mobility modes (walking, bicycle, pedelec): 3-45 min
    max_traveltime_active: TravelTimeLimitActiveMobility = Field(
        default=15,
        description="Maximum travel time in minutes.",
        json_schema_extra=ui_field(
            section="configuration",
            field_order=2,
            label_key="max_traveltime",
            enum_labels=TRAVEL_TIME_LABELS,
            visible_when={
                "$and": [
                    {"routing_mode": {"$in": ["walking", "bicycle", "pedelec"]}},
                    {"measure_type": "time"},
                ]
            },
        ),
    )

    # Travel time for car mode: 3-90 min (only when measure_type is time)
    max_traveltime_car: TravelTimeLimitMotorized = Field(
        default=30,
        description="Maximum travel time in minutes.",
        json_schema_extra=ui_field(
            section="configuration",
            field_order=2,
            label_key="max_traveltime",
            enum_labels=TRAVEL_TIME_LABELS,
            visible_when={
                "$and": [
                    {"routing_mode": "car"},
                    {"measure_type": "time"},
                ]
            },
        ),
    )

    # Travel time for PT mode: 3-90 min (always time-based, no distance option)
    max_traveltime_pt: TravelTimeLimitMotorized = Field(
        default=30,
        description="Maximum travel time in minutes.",
        json_schema_extra=ui_field(
            section="configuration",
            field_order=2,
            label_key="max_traveltime",
            enum_labels=TRAVEL_TIME_LABELS,
            visible_when={"routing_mode": "pt"},
        ),
    )

    # Distance (for non-PT modes when measure_type is distance)
    max_distance: int = Field(
        default=500,
        ge=50,
        le=5000,
        description="Maximum distance in meters.",
        json_schema_extra=ui_field(
            section="configuration",
            field_order=2,
            label_key="max_distance",
            widget="slider",
            widget_options={"min": 50, "max": 5000, "step": 50},
            visible_when={
                "$and": [
                    {"routing_mode": {"$in": ["walking", "bicycle", "pedelec", "car"]}},
                    {"measure_type": "distance"},
                ]
            },
        ),
    )

    steps: CatchmentAreaSteps = Field(
        default=5,
        description="Number of isochrone steps/intervals.",
        json_schema_extra=ui_field(
            section="configuration",
            field_order=3,
            label_key="steps",
        ),
    )

    speed: SpeedKmh = Field(
        default=5,
        description="Travel speed in km/h (for active mobility modes).",
        json_schema_extra=ui_field(
            section="configuration",
            field_order=4,
            label_key="speed",
            enum_labels=SPEED_LABELS,
            visible_when={"routing_mode": {"$in": ["walking", "bicycle", "pedelec"]}},
            widget_options={
                "default_by_field": {
                    "field": "routing_mode",
                    "values": {
                        "walking": 5,
                        "bicycle": 15,
                        "pedelec": 23,
                    },
                }
            },
        ),
    )

    # =========================================================================
    # PT-specific fields (visible only when routing_mode == "pt")
    # Uses same types and translation keys as ÖV-Güteklassen for consistency
    # =========================================================================
    pt_day: Weekday = Field(
        default=Weekday.weekday,
        description="Day type for PT schedule (weekday, saturday, sunday).",
        json_schema_extra=ui_field(
            section="configuration",
            field_order=5,
            label_key="weekday",
            visible_when={"routing_mode": "pt"},
        ),
    )

    pt_start_time: int = Field(
        default=25200,  # 7:00 AM in seconds
        ge=0,
        le=86400,
        description="Start time for PT analysis (seconds from midnight).",
        json_schema_extra=ui_field(
            section="configuration",
            field_order=6,
            label_key="from_time",
            widget="time-picker",
            visible_when={"routing_mode": "pt"},
        ),
    )

    pt_end_time: int = Field(
        default=32400,  # 9:00 AM in seconds
        ge=0,
        le=86400,
        description="End time for PT analysis (seconds from midnight).",
        json_schema_extra=ui_field(
            section="configuration",
            field_order=7,
            label_key="to_time",
            widget="time-picker",
            visible_when={"routing_mode": "pt"},
        ),
    )

    pt_access_mode: AccessEgressMode | None = Field(
        default=AccessEgressMode.walk,
        description="Mode of transport to access PT stations.",
        json_schema_extra=ui_field(
            section="configuration",
            field_order=8,
            label_key="access_mode",
            visible_when={"routing_mode": "pt"},
            advanced=True,
        ),
    )

    pt_egress_mode: AccessEgressMode | None = Field(
        default=AccessEgressMode.walk,
        description="Mode of transport after leaving PT stations.",
        json_schema_extra=ui_field(
            section="configuration",
            field_order=9,
            label_key="pt_egress_mode",
            visible_when={"routing_mode": "pt"},
            advanced=True,
        ),
    )

    # =========================================================================
    # Advanced Configuration
    # =========================================================================
    catchment_area_type: CatchmentAreaType = Field(
        default=CatchmentAreaType.polygon,
        description="Output geometry type for the catchment area.",
        json_schema_extra=ui_field(
            section="configuration",
            field_order=10,
            label_key="catchment_area_type",
            enum_labels=CATCHMENT_AREA_TYPE_LABELS,
            advanced=True,
        ),
    )

    polygon_difference: bool = Field(
        default=True,
        description="If true, polygons show the difference between consecutive isochrone steps.",
        json_schema_extra=ui_field(
            section="configuration",
            field_order=11,
            label_key="polygon_difference",
            advanced=True,
            visible_when={"catchment_area_type": "polygon"},
        ),
    )

    # =========================================================================
    # Scenario Section
    # =========================================================================
    scenario_id: str | None = Field(
        default=None,
        description="Scenario ID to apply network modifications.",
        json_schema_extra=ui_field(
            section="scenario",
            field_order=1,
            widget="scenario-selector",
        ),
    )


class CatchmentAreaToolRunner(BaseToolRunner[CatchmentAreaWindmillParams]):
    """Catchment Area tool runner for Windmill."""

    tool_class = CatchmentAreaTool
    output_geometry_type = "polygon"  # Default, may vary based on catchment_area_type
    default_output_name = "Catchment_Area"

    def get_layer_properties(
        self: Self,
        params: CatchmentAreaWindmillParams,
        metadata: DatasetMetadata,
        table_info: dict[str, Any] | None = None,
    ) -> dict[str, Any] | None:
        """Return style for catchment area with ordinal scale based on minute values.

        Queries unique minute values from the DuckLake table and builds a color_map.
        """
        from goatlib.analysis.schemas.statistics import SortOrder
        from goatlib.analysis.statistics import calculate_unique_values
        from goatlib.tools.style import DEFAULT_POLYGON_STYLE, hex_to_rgb

        # Use 'minute' as the color field
        color_field = "minute"

        # YlGn (Yellow-Green) color palette from Colorbrewer
        # Sequential palette from light yellow-green to dark green
        ylgn_colors = [
            "#FFFFCC",  # Light yellow
            "#D9F0A3",  # Light yellow-green
            "#ADDD8E",  # Yellow-green
            "#78C679",  # Green
            "#41AB5D",  # Medium green
            "#238443",  # Dark green
            "#006837",  # Darker green
            "#004529",  # Darkest green
        ]

        # Query actual unique minute values from the table
        unique_values = []
        if table_info and table_info.get("table_name"):
            try:
                result = calculate_unique_values(
                    con=self.duckdb_con,
                    table_name=table_info["table_name"],
                    attribute=color_field,
                    order=SortOrder.ascendent,
                    limit=9,
                )
                unique_values = [v.value for v in result.values]
                logger.info("Found unique minute values: %s", unique_values)
            except Exception as e:
                logger.warning("Failed to query unique values: %s", e)

        if not unique_values:
            # Fallback: compute expected values from params
            if params.routing_mode in [
                CatchmentAreaRoutingMode.walking,
                CatchmentAreaRoutingMode.bicycle,
                CatchmentAreaRoutingMode.pedelec,
            ]:
                max_value = params.max_traveltime_active
            elif params.routing_mode == CatchmentAreaRoutingMode.car:
                max_value = params.max_traveltime_car
            else:
                max_value = params.max_traveltime_pt

            step_size = max_value / params.steps
            unique_values = [
                int(round(step_size * (i + 1))) for i in range(params.steps)
            ]

        # Select colors based on number of unique values
        num_values = len(unique_values)
        if num_values <= len(ylgn_colors):
            colors = ylgn_colors[:num_values]
        else:
            colors = ylgn_colors

        # Build color_map: [[str(value)], color] for each unique value
        color_map = [
            [[str(val)], colors[i % len(colors)]] for i, val in enumerate(unique_values)
        ]

        return {
            **DEFAULT_POLYGON_STYLE,
            "color": hex_to_rgb(colors[len(colors) // 2]),
            "opacity": 0.8,
            "color_field": {"name": color_field, "type": "number"},
            "color_range": {
                "name": "YlGn",
                "type": "custom",
                "colors": colors,
                "category": "Colorbrewer",
                "color_map": color_map,
            },
            "color_scale": "ordinal",
        }

    def _extract_coordinates_from_layer(
        self: Self,
        layer_id: str,
        user_id: str,
    ) -> tuple[list[float], list[float]]:
        """Extract lat/lon coordinates from a layer.

        Args:
            layer_id: Layer UUID string
            user_id: User UUID string (fallback if layer info unavailable)

        Returns:
            Tuple of (latitudes, longitudes) lists
        """
        # Look up the layer's actual owner to correctly access shared/catalog layers
        layer_owner_id = self.get_layer_owner_id_sync(layer_id)
        if layer_owner_id is None:
            layer_owner_id = user_id  # Fallback to passed user_id
            logger.warning(
                f"Could not find owner for layer {layer_id}, using current user {user_id}"
            )
        elif layer_owner_id != user_id:
            logger.info(
                f"Layer {layer_id} owned by {layer_owner_id}, accessed by {user_id}"
            )

        table_name = self.get_layer_table_path(layer_owner_id, layer_id)

        # Query centroids of all geometries
        result = self.duckdb_con.execute(f"""
            SELECT
                ST_Y(ST_Centroid(geom)) as lat,
                ST_X(ST_Centroid(geom)) as lon
            FROM {table_name}
            WHERE geom IS NOT NULL
        """).fetchall()

        if not result:
            raise ValueError(f"No valid geometries found in layer {layer_id}")

        latitudes = [row[0] for row in result]
        longitudes = [row[1] for row in result]

        logger.info(
            "Extracted %d starting points from layer %s",
            len(latitudes),
            layer_id,
        )

        return latitudes, longitudes

    def _get_starting_coordinates(
        self: Self,
        starting_points: StartingPoints,
        user_id: str,
    ) -> tuple[list[float], list[float]]:
        """Get latitude/longitude coordinates from starting points.

        Args:
            starting_points: Either direct coordinates or layer reference
            user_id: User UUID string (needed for layer lookup)

        Returns:
            Tuple of (latitudes, longitudes) lists
        """
        if isinstance(starting_points, StartingPointsMap):
            # Direct coordinates from map clicks
            return starting_points.latitude, starting_points.longitude
        elif isinstance(starting_points, StartingPointsLayer):
            # Extract from layer
            return self._extract_coordinates_from_layer(
                starting_points.layer_id,
                user_id,
            )
        else:
            raise ValueError(f"Invalid starting_points type: {type(starting_points)}")

    def process(
        self: Self,
        params: CatchmentAreaWindmillParams,
        temp_dir: Path,
    ) -> tuple[Path, DatasetMetadata]:
        """Run catchment area analysis."""
        output_path = temp_dir / "output.parquet"

        # Get coordinates from starting points (either map clicks or layer)
        latitudes, longitudes = self._get_starting_coordinates(
            params.starting_points,
            params.user_id,
        )

        # Build time window for PT routing
        time_window = None
        if params.routing_mode == CatchmentAreaRoutingMode.pt:
            # pt_day is a Weekday enum, get its string value
            weekday_value = (
                params.pt_day.value
                if hasattr(params.pt_day, "value")
                else params.pt_day
            )
            time_window = PTTimeWindow(
                weekday=weekday_value,
                from_time=params.pt_start_time,
                to_time=params.pt_end_time,
            )

        # Get routing URL and auth from settings
        routing_url = None
        authorization = None
        r5_region_mapping_path = None

        if self.settings:
            # Use R5 URL for PT mode, GOAT routing URL for other modes
            if params.routing_mode == CatchmentAreaRoutingMode.pt:
                routing_url = getattr(self.settings, "r5_url", None)
            else:
                routing_url = getattr(self.settings, "goat_routing_url", None)
            authorization = getattr(self.settings, "goat_routing_authorization", None)
            r5_region_mapping_path = getattr(
                self.settings, "r5_region_mapping_path", None
            )

        # Determine travel_time based on routing mode and measure type
        # For distance-based catchment areas, we don't use travel_time
        travel_time: int | None = None
        # Determine travel_time/travel_distance based on routing mode and measure type
        travel_time: int | None = None

        if params.routing_mode in [
            CatchmentAreaRoutingMode.walking,
            CatchmentAreaRoutingMode.bicycle,
            CatchmentAreaRoutingMode.pedelec,
        ]:
            # Active mobility modes support both time and distance
            if params.measure_type == CatchmentAreaMeasureType.distance:
                # TODO: CatchmentAreaToolParams doesn't support travel_distance yet
                # For now, convert distance to approximate time using speed
                # distance (m) / speed (km/h) * 60 / 1000 = time (min)
                speed_kmh = params.speed or 5  # Default walking speed
                travel_time = int(params.max_distance / (speed_kmh * 1000 / 60))
                logger.info(
                    "Converting distance %dm to ~%d min at %d km/h",
                    params.max_distance,
                    travel_time,
                    speed_kmh,
                )
            else:
                travel_time = params.max_traveltime_active
        elif params.routing_mode == CatchmentAreaRoutingMode.car:
            # Car mode supports both time and distance
            if params.measure_type == CatchmentAreaMeasureType.distance:
                # Convert distance to approximate time (assume ~50 km/h average)
                travel_time = int(params.max_distance / (50 * 1000 / 60))
                logger.info(
                    "Converting distance %dm to ~%d min at 50 km/h (car)",
                    params.max_distance,
                    travel_time,
                )
            else:
                travel_time = params.max_traveltime_car
        else:
            # PT mode - always time-based
            travel_time = params.max_traveltime_pt

        # Build analysis params
        analysis_params = CatchmentAreaToolParams(
            latitude=latitudes,
            longitude=longitudes,
            routing_mode=params.routing_mode,
            travel_time=travel_time or 15,  # Fallback
            steps=params.steps,
            speed=params.speed,
            transit_modes=params.pt_modes,
            time_window=time_window,
            access_mode=params.pt_access_mode or AccessEgressMode.walk,
            egress_mode=params.pt_egress_mode or AccessEgressMode.walk,
            catchment_area_type=params.catchment_area_type,
            polygon_difference=params.polygon_difference,
            scenario_id=params.scenario_id,
            output_path=str(output_path),
            routing_url=routing_url,
            authorization=authorization,
            r5_region_mapping_path=r5_region_mapping_path,
        )

        # Run the analysis tool
        tool = self.tool_class()
        try:
            results = tool.run(analysis_params)
            result_path, metadata = results[0]
            return Path(result_path), metadata
        finally:
            tool.cleanup()


def main(params: CatchmentAreaWindmillParams) -> dict:
    """Windmill entry point for catchment area tool."""
    runner = CatchmentAreaToolRunner()
    runner.init_from_env()

    try:
        return runner.run(params)
    finally:
        runner.cleanup()
