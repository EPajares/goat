# type: ignore

import math
import time
import uuid
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np
import polars as pl
from redis import Redis
from routing.core.config import settings
from routing.core.isochrone import compute_isochrone, compute_isochrone_h3
from routing.core.jsoline import generate_jsolines
from routing.core.street_network.street_network_util import StreetNetworkUtil
from routing.schemas.catchment_area import (
    BICYCLE_SPEED_FOOTWAYS,
    H3_CELL_RESOLUTION,
    SEGMENT_DATA_SCHEMA,
    VALID_BICYCLE_CLASSES,
    VALID_CAR_CLASSES,
    VALID_WALKING_CLASSES,
    VALID_WHEELCHAIR_CLASSES,
    CatchmentAreaRoutingTypeActiveMobility,
    CatchmentAreaRoutingTypeCar,
    CatchmentAreaTravelTimeCostActiveMobility,
    CatchmentAreaTravelTimeCostMotorizedMobility,
    ICatchmentAreaActiveMobility,
    ICatchmentAreaCar,
)
from routing.schemas.error import BufferExceedsNetworkError, DisconnectedOriginError
from routing.schemas.status import ProcessingStatus
from routing.utils import format_value_null_sql
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


class CRUDCatchmentArea:
    def __init__(self, db_connection: AsyncSession, redis: Optional[Redis]) -> None:
        self.db_connection = db_connection
        self.redis = redis
        self.routing_network: Optional[Dict[Any, pl.DataFrame]] = None

    async def read_network(
        self,
        routing_network: Dict[Any, pl.DataFrame],
        obj_in: Union[ICatchmentAreaActiveMobility, ICatchmentAreaCar],
        input_table: str,
        num_points: int,
        origin_point_cell_resolution: int,
    ) -> Tuple[Dict[str, np.ndarray], str, List[int], List[int], List[str]]:
        """Read relevant sub-network for catchment area calculation from polars dataframe."""
        # Get valid segment classes based on transport mode
        valid_segment_classes: List[str]
        if type(obj_in) is ICatchmentAreaActiveMobility:
            if obj_in.routing_type == CatchmentAreaRoutingTypeActiveMobility.walking:
                valid_segment_classes = VALID_WALKING_CLASSES
            elif obj_in.routing_type == CatchmentAreaRoutingTypeActiveMobility.bicycle:
                valid_segment_classes = VALID_BICYCLE_CLASSES
            elif obj_in.routing_type == CatchmentAreaRoutingTypeActiveMobility.pedelec:
                valid_segment_classes = VALID_BICYCLE_CLASSES
            elif (
                obj_in.routing_type == CatchmentAreaRoutingTypeActiveMobility.wheelchair
            ):
                valid_segment_classes = VALID_WHEELCHAIR_CLASSES
            else:
                raise ValueError(f"Invalid routing type: {obj_in.routing_type}")
        else:
            if obj_in.routing_type == CatchmentAreaRoutingTypeCar.car:
                valid_segment_classes = VALID_CAR_CLASSES
            else:
                raise ValueError(f"Invalid routing type: {obj_in.routing_type}")
        # Compute buffer distance for identifying relevant H3_6 cells
        buffer_dist: Union[float, int]
        if type(obj_in.travel_cost) is CatchmentAreaTravelTimeCostActiveMobility:
            buffer_dist = obj_in.travel_cost.max_traveltime * (
                (obj_in.travel_cost.speed * 1000) / 60
            )
        elif type(obj_in.travel_cost) is CatchmentAreaTravelTimeCostMotorizedMobility:
            buffer_dist = obj_in.travel_cost.max_traveltime * (
                (settings.CATCHMENT_AREA_CAR_BUFFER_DEFAULT_SPEED * 1000) / 60
            )
        else:
            # Type of travel cost is CatchmentAreaDistanceCost
            buffer_dist = obj_in.travel_cost.max_distance
        # Identify H3_3 & H3_6 cells relevant to this catchment area calculation
        h3_3_cells: set[str] = set()
        h3_6_cells: set[str] = set()
        sql_get_relevant_cells = text(
            f"""
            WITH point AS (
                SELECT geom FROM {input_table} LIMIT {num_points}
            ),
            buffer AS (
                SELECT ST_Buffer(point.geom::geography, {buffer_dist})::geometry AS geom
                FROM point
            ),
            cells AS (
                SELECT
                    basic.to_short_h3_6(h3_index::bigint) AS h3_6,
                    basic.to_short_h3_3(h3_lat_lng_to_cell(ST_Centroid(h3_geom)::point, 3)::bigint) AS h3_3
                FROM buffer,
                LATERAL basic.fill_polygon_h3_6(buffer.geom)
            )
            SELECT h3_3, ARRAY_AGG(h3_6) AS h3_6
            FROM cells
            GROUP BY h3_3;
        """
        )
        result = (await self.db_connection.execute(sql_get_relevant_cells)).fetchall()
        for h3_3_cell_data in result:
            h3_3_cells.add(h3_3_cell_data[0])
            for h3_6_cell in h3_3_cell_data[1]:
                h3_6_cells.add(h3_6_cell)
        # Get relevant segments & connectors
        sub_network: pl.DataFrame = pl.DataFrame()
        for h3_3 in h3_3_cells:
            sub_df: Optional[pl.DataFrame] = routing_network.get(h3_3)
            if sub_df is None:
                raise BufferExceedsNetworkError(
                    "Catchment area buffer exceeds available H3_3 network cells."
                )
            sub_df = sub_df.filter(
                pl.col("h3_6").is_in(h3_6_cells)
                & pl.col("class_").is_in(valid_segment_classes)
            )
            # For active mobility routing, consider "primary" edges only if they have appropriate speed limits
            if type(obj_in) is ICatchmentAreaActiveMobility:
                sub_df = sub_df.filter(
                    (pl.col("class_") != "primary")
                    | (
                        (
                            pl.col("maxspeed_forward").is_not_null()
                            & (pl.col("maxspeed_forward") <= 50)
                        )
                        | (
                            pl.col("maxspeed_backward").is_not_null()
                            & (pl.col("maxspeed_backward") <= 50)
                        )
                    )
                )
            if sub_network.width > 0:
                sub_network.extend(sub_df)
            else:
                sub_network = sub_df
        # Produce all network modifications required to apply the specified scenario
        network_modifications_table: Optional[str] = None
        if obj_in.scenario_id:
            sql_produce_network_modifications = text(
                f"""
                    SELECT basic.produce_network_modifications(
                        {format_value_null_sql(obj_in.scenario_id)},
                        {obj_in.street_network.edge_layer_project_id},
                        {obj_in.street_network.node_layer_project_id}
                    );
                """
            )
            network_modifications_table = (
                await self.db_connection.execute(sql_produce_network_modifications)
            ).fetchone()[0]
        if network_modifications_table:
            # Apply network modifications to the sub-network
            segments_to_discard: List[int] = []
            sql_get_network_modifications = text(
                f"""
                SELECT edit_type, id, class_, source, target,
                    length_m, length_3857, CAST(coordinates_3857 AS TEXT) AS coordinates_3857,
                    impedance_slope, impedance_slope_reverse, impedance_surface, maxspeed_forward,
                    maxspeed_backward, h3_6, h3_3
                FROM "{network_modifications_table}";
            """
            )
            result_modifications = (
                await self.db_connection.execute(sql_get_network_modifications)
            ).fetchall()
            for modification in result_modifications:
                if modification[0] == "d":
                    segments_to_discard.append(modification[1])
                    continue
                new_segment = pl.DataFrame(
                    [
                        {
                            "id": modification[1],
                            "length_m": modification[5],
                            "length_3857": modification[6],
                            "class_": modification[2],
                            "impedance_slope": modification[8],
                            "impedance_slope_reverse": modification[9],
                            "impedance_surface": modification[10],
                            "coordinates_3857": modification[7],
                            "maxspeed_forward": modification[11],
                            "maxspeed_backward": modification[12],
                            "source": modification[3],
                            "target": modification[4],
                            "h3_3": modification[13],
                            "h3_6": modification[14],
                        }
                    ],
                    schema_overrides=SEGMENT_DATA_SCHEMA,  # type: ignore
                )
                new_segment = new_segment.with_columns(
                    pl.col("coordinates_3857").str.json_decode()
                )
                sub_network.extend(new_segment)
            # Remove segments which are deleted or modified due to the scenario
            sub_network = sub_network.filter(~pl.col("id").is_in(segments_to_discard))
        # Create necessary artifical segments and add them to our sub network
        origin_point_connectors: List[int] = []
        origin_point_cell_index: List[int] = []
        origin_point_h3_3: List[str] = []
        segments_to_discard = []
        additional_filters: str = ""
        if type(obj_in) is ICatchmentAreaActiveMobility:
            additional_filters = "AND (class_ != ''primary'' OR s.maxspeed_forward <= 50 OR s.maxspeed_backward <= 50)"
        sql_get_artificial_segments = text(
            f"""
            SELECT
                point_id,
                old_id,
                id, length_m, length_3857, class_, impedance_slope,
                impedance_slope_reverse, impedance_surface,
                CAST(coordinates_3857 AS TEXT) AS coordinates_3857,
                maxspeed_forward, maxspeed_backward, source, target,
                h3_3, h3_6, point_cell_index, point_h3_3
            FROM basic.get_artificial_segments(
                {format_value_null_sql(settings.BASE_STREET_NETWORK)},
                {format_value_null_sql(network_modifications_table)},
                {format_value_null_sql(input_table)},
                {num_points},
                '{",".join(valid_segment_classes)}',
                {origin_point_cell_resolution},
                '{additional_filters}'
            );
        """
        )
        result_artificial_segments = (
            await self.db_connection.execute(sql_get_artificial_segments)
        ).fetchall()  # TODO Check if artificial segments are even required for car routing
        for a_seg in result_artificial_segments:
            if (
                a_seg[0] is not None
            ):  # point_id is not null, indicating a new artificial segment
                origin_point_connectors.append(a_seg[12])  # type: ignore
                origin_point_cell_index.append(a_seg[16])  # type: ignore
                origin_point_h3_3.append(a_seg[17])  # type: ignore
                segments_to_discard.append(a_seg[1])
            new_df = pl.DataFrame(
                [
                    {
                        "id": a_seg[2],
                        "length_m": a_seg[3],
                        "length_3857": a_seg[4],
                        "class_": a_seg[5],
                        "impedance_slope": a_seg[6],
                        "impedance_slope_reverse": a_seg[7],
                        "impedance_surface": a_seg[8],
                        "coordinates_3857": a_seg[9],
                        "maxspeed_forward": a_seg[10],
                        "maxspeed_backward": a_seg[11],
                        "source": a_seg[12],
                        "target": a_seg[13],
                        "h3_3": a_seg[14],
                        "h3_6": a_seg[15],
                    }
                ],
                schema_overrides=SEGMENT_DATA_SCHEMA,  # type: ignore
            )
            new_df = new_df.with_columns(pl.col("coordinates_3857").str.json_decode())
            sub_network.extend(new_df)
        if len(origin_point_connectors) == 0:
            raise DisconnectedOriginError(
                "Starting point(s) are disconnected from the street network."
            )
        # Remove segments which are replaced by artificial segments or modified due to the scenario
        sub_network = sub_network.filter(~pl.col("id").is_in(segments_to_discard))
        # Replace all NULL values in the impedance columns with 0
        sub_network = sub_network.with_columns(pl.col("impedance_surface").fill_null(0))
        # Compute cost for each segment
        if type(obj_in.travel_cost) in [
            CatchmentAreaTravelTimeCostActiveMobility,
            CatchmentAreaTravelTimeCostMotorizedMobility,
        ]:
            # If producing a travel time cost based catchment area, compute segment cost accordingly
            calculated_speed: Optional[float] = None
            if type(obj_in.travel_cost) is CatchmentAreaTravelTimeCostActiveMobility:
                calculated_speed = obj_in.travel_cost.speed / 3.6
            sub_network = self.compute_segment_cost(
                sub_network=sub_network,
                mode=obj_in.routing_type,
                speed=calculated_speed,
            )
        else:
            # TODO: Refactor this into a separate function as slope / surface impedance should be included
            # for bicycle / pedelec routing and one-ways should be avoided for car routing
            # If producing a distance cost based catchment area, use the segment length as cost
            sub_network = sub_network.with_columns(
                pl.col("length_m").alias("cost"),
                pl.col("length_m").alias("reverse_cost"),
            )
        # Select columns required for computing catchment area and convert to dictionary of numpy arrays
        sub_network_dict: Dict[str, np.ndarray] = {
            "id": sub_network.get_column("id").to_numpy().copy(),
            "source": sub_network.get_column("source").to_numpy().copy(),
            "target": sub_network.get_column("target").to_numpy().copy(),
            "cost": sub_network.get_column("cost").to_numpy().copy(),
            "reverse_cost": sub_network.get_column("reverse_cost").to_numpy().copy(),
            "length": sub_network.get_column("length_3857").to_numpy().copy(),
            "geom": sub_network.get_column("coordinates_3857").to_numpy().copy(),
        }
        return (
            sub_network_dict,
            network_modifications_table,  # type: ignore
            origin_point_connectors,
            origin_point_cell_index,
            origin_point_h3_3,
        )

    async def create_input_table(
        self, obj_in: Union[ICatchmentAreaActiveMobility, ICatchmentAreaCar]
    ) -> Tuple[str, int]:
        """Create the input table for the catchment area calculation."""
        # Generate random table name
        table_name: str = str(uuid.uuid4()).replace("-", "_")
        table_name = f'temporal."{table_name}"'
        # Create temporary table for storing catchment area starting points
        await self.db_connection.execute(
            text(
                f"""
                CREATE TABLE {table_name} (
                    id serial PRIMARY KEY,
                    geom geometry(Point, 4326)
                );
            """
            )
        )
        # Insert catchment area starting points into the temporary table
        insert_string: str = ""
        for i in range(len(obj_in.starting_points.latitude)):
            latitude: float = obj_in.starting_points.latitude[i]
            longitude: float = obj_in.starting_points.longitude[i]
            insert_string += f"SELECT ST_SetSRID(ST_MakePoint({longitude}, {latitude}), 4326) AS geom UNION "
        await self.db_connection.execute(
            text(
                f"""
                INSERT INTO {table_name} (geom)
                WITH clusters AS (
                    SELECT
                        ST_ClusterDBSCAN(
                            ST_Transform(geom, 3857),
                            eps := 5,
                            minpoints := 1
                        ) OVER () AS cluster_id,
                        geom
                    FROM (
                        {insert_string.rstrip("UNION ")}
                    ) AS points
                )
                SELECT ST_Centroid(ST_Collect(geom)) AS merged_geom
                FROM clusters
                GROUP BY cluster_id;
            """
            )
        )
        await self.db_connection.commit()
        # Get actual count of starting points
        sql_get_count = text(f"SELECT COUNT(*) FROM {table_name};")
        num_points: int = (await self.db_connection.execute(sql_get_count)).fetchone()[
            0
        ]  # type: ignore
        return table_name, num_points

    async def drop_temp_tables(
        self, input_table: str, network_modifications_table: Optional[str]
    ) -> None:
        """Delete the temporary input and network modifications tables."""
        await self.db_connection.execute(text(f"DROP TABLE {input_table};"))
        if network_modifications_table is not None:
            await self.db_connection.execute(
                text(f'DROP TABLE "{network_modifications_table}";')
            )
        await self.db_connection.commit()

    def compute_segment_cost(
        self,
        sub_network: pl.DataFrame,
        mode: Union[
            CatchmentAreaRoutingTypeActiveMobility, CatchmentAreaRoutingTypeCar
        ],
        speed: Optional[float],
    ) -> pl.DataFrame:
        """Compute the cost of a segment based on the mode, speed, impedance, etc."""
        if mode == CatchmentAreaRoutingTypeActiveMobility.walking:
            if speed is None:
                raise ValueError("Speed must be provided for walking mode.")
            return sub_network.with_columns(
                (pl.col("length_m") / speed).alias("cost"),
                (pl.col("length_m") / speed).alias("reverse_cost"),
            )
        elif mode == CatchmentAreaRoutingTypeActiveMobility.bicycle:
            if speed is None:
                raise ValueError("Speed must be provided for bicycle mode.")
            return sub_network.with_columns(
                pl.when(
                    (pl.col("class_") != "pedestrian")
                    & (pl.col("class_") != "crosswalk")
                )
                .then(
                    (
                        pl.col("length_m")
                        * (1 + pl.col("impedance_slope") + pl.col("impedance_surface"))
                    )
                    / speed
                )
                .otherwise(
                    pl.col("length_m") / (BICYCLE_SPEED_FOOTWAYS / 3.6)
                )  # This calculation is invoked when the segment class requires cyclists to walk their bicycle
                .alias("cost"),
                pl.when(
                    (pl.col("class_") != "pedestrian")
                    & (pl.col("class_") != "crosswalk")
                )
                .then(
                    (
                        pl.col("length_m")
                        * (
                            1
                            + pl.col("impedance_slope_reverse")
                            + pl.col("impedance_surface")
                        )
                    )
                    / speed
                )
                .otherwise(
                    pl.col("length_m") / (BICYCLE_SPEED_FOOTWAYS / 3.6)
                )  # This calculation is invoked when the segment class requires cyclists to walk their bicycle
                .alias("reverse_cost"),
            )
        elif mode == CatchmentAreaRoutingTypeActiveMobility.pedelec:
            if speed is None:
                raise ValueError("Speed must be provided for pedelec mode.")
            return sub_network.with_columns(
                pl.when(
                    (pl.col("class_") != "pedestrian")
                    & (pl.col("class_") != "crosswalk")
                )
                .then((pl.col("length_m") * (1 + pl.col("impedance_surface"))) / speed)
                .otherwise(
                    pl.col("length_m") / (BICYCLE_SPEED_FOOTWAYS / 3.6)
                )  # This calculation is invoked when the segment class requires cyclists to walk their pedelec
                .alias("cost"),
                pl.when(
                    (pl.col("class_") != "pedestrian")
                    & (pl.col("class_") != "crosswalk")
                )
                .then((pl.col("length_m") * (1 + pl.col("impedance_surface"))) / speed)
                .otherwise(
                    pl.col("length_m") / (BICYCLE_SPEED_FOOTWAYS / 3.6)
                )  # This calculation is invoked when the segment class requires cyclists to walk their pedelec
                .alias("reverse_cost"),
            )
        elif mode == CatchmentAreaRoutingTypeActiveMobility.wheelchair:
            if speed is None:
                raise ValueError("Speed must be provided for wheelchair mode.")
            return sub_network.with_columns(
                (pl.col("length_m") / speed).alias("cost"),
                (pl.col("length_m") / speed).alias("reverse_cost"),
            )
        elif mode == CatchmentAreaRoutingTypeCar.car:
            return sub_network.with_columns(
                (pl.col("length_m") / ((pl.col("maxspeed_forward") * 0.7) / 3.6)).alias(
                    "cost"
                ),
                pl.when(pl.col("maxspeed_backward").is_not_null())
                .then(pl.col("length_m") / ((pl.col("maxspeed_backward") * 0.7) / 3.6))
                .otherwise(
                    99999
                )  # This is a one-way segment, so assign a very high cost to the reverse direction
                .alias("reverse_cost"),
            )
        else:
            raise ValueError(f"Invalid routing type for cost computation: {mode}")

    async def get_h3_10_grid(
        self,
        db_connection: AsyncSession,
        obj_in: Union[ICatchmentAreaActiveMobility, ICatchmentAreaCar],
        origin_h3_10: List[str],
    ) -> Tuple[List[str], np.ndarray, np.ndarray]:
        """Get H3_10 cell grid required for computing a grid-type catchment area."""
        # Compute buffer distance for identifying relevant H3_10 cells
        buffer_dist: Union[float, int]
        if type(obj_in.travel_cost) is CatchmentAreaTravelTimeCostActiveMobility:
            buffer_dist = obj_in.travel_cost.max_traveltime * (
                (obj_in.travel_cost.speed * 1000) / 60
            )
        elif type(obj_in.travel_cost) is CatchmentAreaTravelTimeCostMotorizedMobility:
            buffer_dist = obj_in.travel_cost.max_traveltime * (
                (settings.CATCHMENT_AREA_CAR_BUFFER_DEFAULT_SPEED * 1000) / 60
            )
        else:
            # Type of travel cost is CatchmentAreaDistanceCost
            buffer_dist = obj_in.travel_cost.max_distance
        # Fetch H3_10 cell grid relevant to the catchment area calculation
        origin_h3_10_str = ", ".join(f"'{h}'" for h in origin_h3_10)
        sql_get_relevant_cells = text(
            f"""
            WITH cells AS (
                SELECT DISTINCT(h3_grid_disk(sub.origin_h3_index, radius.value)) AS h3_index
                FROM (SELECT UNNEST(ARRAY[{origin_h3_10_str}]::h3index[]) AS origin_h3_index) sub,
                LATERAL (SELECT ({buffer_dist}::int / (h3_get_hexagon_edge_length_avg(10, 'm') * 1.5)::int) AS value) AS radius
            )
            SELECT h3_index, ST_X(centroid), ST_Y(centroid)
            FROM cells,
            LATERAL (
                SELECT ST_Transform(ST_SetSRID(point::geometry, 4326), 3857) AS centroid
                FROM h3_cell_to_lat_lng(h3_index) AS point
            ) sub;
        """
        )
        result = (await db_connection.execute(sql_get_relevant_cells)).fetchall()
        h3_index: List[str] = [r[0] for r in result]
        x_centroids: np.ndarray = np.array([r[1] for r in result])
        y_centroids: np.ndarray = np.array([r[2] for r in result])
        return h3_index, x_centroids, y_centroids

    async def save_result(
        self,
        obj_in: Union[ICatchmentAreaActiveMobility, ICatchmentAreaCar],
        shapes: Any,
        network: Any,
        grid_index: Optional[List[str]],
        grid: Optional[np.ndarray],
    ) -> None:
        """Save the result of the catchment area computation to the database."""
        # Compute step size for the catchment area
        step_size: Union[float, int]
        if type(obj_in.travel_cost) in [
            CatchmentAreaTravelTimeCostActiveMobility,
            CatchmentAreaTravelTimeCostMotorizedMobility,
        ]:
            step_size = obj_in.travel_cost.max_traveltime / obj_in.travel_cost.steps
        else:
            step_size = obj_in.travel_cost.max_distance / obj_in.travel_cost.steps
        if obj_in.catchment_area_type == "polygon":
            # Save catchment area geometry data (shapes)
            # Assuming shapes is a dictionary with a 'full' key that points to a pandas DataFrame
            # which has 'geometry' and 'minute' columns.
            shapes = shapes["full"]
            insert_string: str = ""
            for i in shapes.index:
                geom: str = shapes["geometry"][i]
                minute: Union[float, int] = shapes["minute"][i]
                insert_string += f"SELECT ST_MakeValid(ST_SetSRID(ST_GeomFromText('{geom}'), 4326)) AS geom, {minute} AS minute UNION ALL "
            insert_string, _, _ = insert_string.rpartition(" UNION ALL ")
            sql_insert_into_table = text(
                f"""
                WITH isochrones AS
                (
                    SELECT p."minute", (ST_DUMP(p.geom)).geom
                    FROM (
                        {insert_string}
                    ) p
                ),
                isochrones_filled AS
                (
                    SELECT "minute", ST_COLLECT(ST_MAKEPOLYGON(ST_ExteriorRing(geom))) AS orig_geom, ST_COLLECT(filled) AS filled_geom
                    FROM isochrones,
                    LATERAL basic.fill_polygon_holes(geom, {settings.CATCHMENT_AREA_HOLE_THRESHOLD_SQM}) filled
                    GROUP BY "minute"
                    ORDER BY "minute" DESC
                ),
                isochrones_with_id AS
                (
                    SELECT row_number() over() id, *
                    FROM isochrones_filled
                )
                INSERT INTO {obj_in.result_table} (layer_id, geom, integer_attr1)
                SELECT '{obj_in.layer_id}', ST_MakeValid(COALESCE(j.geom, a.filled_geom)) AS geom, ROUND(a."minute")
                FROM isochrones_with_id a
                LEFT JOIN LATERAL
                (
                    SELECT ST_DIFFERENCE(a.filled_geom, b.filled_geom) AS geom
                    FROM isochrones_with_id b
                    WHERE a.id + 1 = b.id
                ) j ON {"TRUE" if obj_in.polygon_difference else "FALSE"};
            """
            )
            try:
                await self.db_connection.execute(sql_insert_into_table)
                await self.db_connection.commit()
            except Exception as e:
                raise Exception(
                    f"Error inserting into table {obj_in.result_table}: {str(e).splitlines()[:5]}"
                ) from e
        elif obj_in.catchment_area_type == "network":
            # Save catchment area network data
            # Assuming network is a dictionary with a 'features' key that points to a list of dicts.
            if network is None:
                raise ValueError(
                    "Network data is required for 'network' catchment area type."
                )
            for batch_index in range(
                0, len(network["features"]), settings.DATA_INSERT_BATCH_SIZE
            ):
                insert_string = ""
                for i in range(
                    batch_index,
                    min(
                        len(network["features"]),
                        batch_index + settings.DATA_INSERT_BATCH_SIZE,
                    ),
                ):
                    coordinates: List[List[float]] = network["features"][i]["geometry"][
                        "coordinates"
                    ]
                    cost: float = (
                        math.ceil(
                            network["features"][i]["properties"]["cost"] / step_size
                        )
                        * step_size
                    )
                    points_string: str = ""
                    for pair in coordinates:
                        points_string += f"ST_MakePoint({pair[0]}, {pair[1]}),"
                    insert_string += f"""(
                        '{obj_in.layer_id}',
                        ST_Transform(ST_SetSRID(ST_MakeLine(ARRAY[{points_string.rstrip(',')}]), 3857), 4326),
                        {round(cost)}
                    ),"""
                # Check if insert_string is not empty before attempting to insert
                if insert_string:
                    insert_command = text(
                        f"""
                        INSERT INTO {obj_in.result_table} (layer_id, geom, integer_attr1)
                        VALUES {insert_string.rstrip(",")};
                    """
                    )
                    try:
                        await self.db_connection.execute(insert_command)
                        await self.db_connection.commit()
                    except Exception as e:
                        raise Exception(
                            f"Error inserting into table {obj_in.result_table}: {str(e).splitlines()[:5]}"
                        ) from e
        else:  # obj_in.catchment_area_type == "rectangular_grid"
            # Save catchment area grid data
            if grid_index is None or grid is None:
                raise ValueError(
                    "Grid index and grid data are required for 'rectangular_grid' catchment area type."
                )
            for batch_index in range(
                0, len(grid_index), settings.DATA_INSERT_BATCH_SIZE
            ):
                insert_string = ""
                for i in range(
                    batch_index,
                    min(len(grid_index), batch_index + settings.DATA_INSERT_BATCH_SIZE),
                ):
                    if math.isnan(grid[i]):
                        continue
                    cost = math.ceil(grid[i] / step_size) * step_size
                    insert_string += f"""(
                        '{obj_in.layer_id}',
                        ST_SetSRID(h3_cell_to_boundary('{grid_index[i]}'::h3index)::geometry, 4326),
                        '{grid_index[i]}',
                        {round(cost)}
                    ),"""
                # Insert only if any grid data was added to the query in this batch
                if insert_string:
                    insert_command = text(
                        f"""
                        INSERT INTO {obj_in.result_table} (layer_id, geom, text_attr1, integer_attr1)
                        VALUES {insert_string.rstrip(",")};
                    """
                    )
                    try:
                        await self.db_connection.execute(insert_command)
                        await self.db_connection.commit()
                    except Exception as e:
                        raise Exception(
                            f"Error inserting into table {obj_in.result_table}: {str(e).splitlines()[:5]}"
                        ) from e

    async def run(self, obj_in_dict: Dict[str, Any]) -> None:
        """Compute catchment areas for the given request parameters."""
        obj_in: Union[ICatchmentAreaActiveMobility, ICatchmentAreaCar]
        if obj_in_dict["routing_type"] != CatchmentAreaRoutingTypeCar.car.value:
            obj_in = ICatchmentAreaActiveMobility(**obj_in_dict)
        else:
            obj_in = ICatchmentAreaCar(**obj_in_dict)
        # Fetch routing network (processed segments) and load into memory
        if self.routing_network is None:
            self.routing_network, _ = await StreetNetworkUtil(self.db_connection).fetch(
                edge_layer_id=settings.BASE_STREET_NETWORK,
                node_layer_id=None,
                region_geofence=f"SELECT * FROM {settings.NETWORK_REGION_TABLE}",
            )
        routing_network: Dict[Any, pl.DataFrame] = self.routing_network
        total_start: float = time.time()
        # Read & process routing network to extract relevant sub-network
        start_time: float = time.time()
        sub_routing_network: Optional[Dict[str, np.ndarray]] = None
        origin_connector_ids: Optional[List[int]] = None
        input_table: str = ""
        network_modifications_table: Optional[str] = None
        origin_point_h3_10: List[str] = []
        try:
            # Create input table for catchment area origin points
            input_table, num_points = await self.create_input_table(obj_in)
            # Read & process routing network to extract relevant sub-network
            (
                sub_routing_network,
                network_modifications_table,
                origin_connector_ids,
                _,  # Type is origin_point_cell_index, not used here
                origin_point_h3_10,
            ) = await self.read_network(
                routing_network,
                obj_in,
                input_table,
                num_points,
                H3_CELL_RESOLUTION[obj_in.routing_type],
            )
            # Delete input table for catchment area origin points
            await self.drop_temp_tables(input_table, network_modifications_table)
        except Exception as e:
            if self.redis:
                self.redis.set(str(obj_in.layer_id), ProcessingStatus.failure.value)
            await self.db_connection.rollback()
            if type(e) == DisconnectedOriginError:
                if self.redis:
                    self.redis.set(
                        str(obj_in.layer_id), ProcessingStatus.disconnected_origin.value
                    )
            print(e)
            return
        print(f"Network read time: {round(time.time() - start_time, 2)} sec")
        # Compute catchment area utilizing processed sub-network
        start_time = time.time()
        catchment_area_grid: Optional[np.ndarray] = None
        catchment_area_network: Any = None
        catchment_area_shapes: Any = None
        try:
            is_travel_time_catchment_area: bool = type(obj_in.travel_cost) in [
                CatchmentAreaTravelTimeCostActiveMobility,
                CatchmentAreaTravelTimeCostMotorizedMobility,
            ]
            speed: Optional[float] = None
            if (
                type(obj_in) is ICatchmentAreaActiveMobility
                and is_travel_time_catchment_area
            ):
                speed = obj_in.travel_cost.speed / 3.6

            zoom: int
            if type(obj_in) is ICatchmentAreaActiveMobility:
                zoom = 13
            else:
                zoom = 11  # Use lower resolution grid for car catchment areas

            catchment_area_grid_index: Optional[List[str]] = None

            if sub_routing_network is None or origin_connector_ids is None:
                raise ValueError(
                    "Sub-routing network or origin connectors are not initialized."
                )

            if obj_in.catchment_area_type != "rectangular_grid":
                catchment_area_grid, catchment_area_network = compute_isochrone(
                    edge_network_input=sub_routing_network,
                    start_vertices=origin_connector_ids,
                    travel_time=(
                        obj_in.travel_cost.max_traveltime
                        if is_travel_time_catchment_area
                        else obj_in.travel_cost.max_distance
                    ),
                    speed=speed,
                    zoom=zoom,
                    is_distance_based=(not is_travel_time_catchment_area),
                )
            else:
                (
                    catchment_area_grid_index,
                    h3_centroid_x,
                    h3_centroid_y,
                ) = await self.get_h3_10_grid(
                    self.db_connection,
                    obj_in=obj_in,
                    origin_h3_10=origin_point_h3_10,
                )
                catchment_area_grid = compute_isochrone_h3(
                    edge_network_input=sub_routing_network,
                    start_vertices=origin_connector_ids,
                    travel_time=(
                        obj_in.travel_cost.max_traveltime
                        if is_travel_time_catchment_area
                        else obj_in.travel_cost.max_distance
                    ),
                    speed=speed,
                    centroid_x=h3_centroid_x,
                    centroid_y=h3_centroid_y,
                    zoom=zoom,
                    is_distance_based=(not is_travel_time_catchment_area),
                )
            print("Computed catchment area grid & network.")
            if obj_in.catchment_area_type == "polygon":
                if catchment_area_grid is None:
                    raise ValueError(
                        "Catchment area grid is required to generate jsolines."
                    )
                catchment_area_shapes = generate_jsolines(
                    grid=catchment_area_grid,
                    travel_time=(
                        obj_in.travel_cost.max_traveltime
                        if is_travel_time_catchment_area
                        else obj_in.travel_cost.max_distance
                    ),
                    percentile=5,
                    steps=obj_in.travel_cost.steps,
                )
                print("Computed catchment area shapes.")
        except Exception as e:
            if self.redis:
                self.redis.set(str(obj_in.layer_id), ProcessingStatus.failure.value)
            print(e)
            return
        print(
            f"Catchment area computation time: {round(time.time() - start_time, 2)} sec"
        )
        # Write output of catchment area computation to database
        start_time = time.time()
        try:
            await self.save_result(
                obj_in,
                catchment_area_shapes,
                catchment_area_network,
                catchment_area_grid_index,
                catchment_area_grid,
            )
        except Exception as e:
            if self.redis:
                self.redis.set(str(obj_in.layer_id), ProcessingStatus.failure.value)
            await self.db_connection.rollback()
            print(e)
            return
        print(f"Result save time: {round(time.time() - start_time, 2)} sec")
        print(f"Total time: {round(time.time() - total_start, 2)} sec")
        if self.redis:
            self.redis.set(str(obj_in.layer_id), ProcessingStatus.success.value)
