# type: ignore

import asyncio
import math
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np
from routing.core.config import settings
from routing.core.isochrone import (  # type: ignore
    construct_adjacency_list_,
    dijkstra_h3,
    network_to_grid_h3,
    prepare_network_isochrone,
)
from routing.core.street_network.street_network_util import StreetNetworkUtil
from routing.crud.crud_catchment_area import CRUDCatchmentArea
from routing.db.session import async_session
from routing.schemas.catchment_area import (
    CatchmentAreaRoutingTypeActiveMobility,
    CatchmentAreaRoutingTypeCar,
    CatchmentAreaStartingPoints,
    CatchmentAreaStreetNetwork,
    CatchmentAreaType,
    ICatchmentAreaActiveMobility,
    ICatchmentAreaCar,
)
from routing.schemas.error import BufferExceedsNetworkError, DisconnectedOriginError
from routing.schemas.heatmap import (
    MATRIX_RESOLUTION_CONFIG,
    ROUTING_COST_CONFIG,
)
from routing.utils import print_error, print_info
from sqlalchemy import Executable, text
from sqlalchemy.ext.asyncio import AsyncSession
from tqdm import tqdm


class HeatmapMatrixProcess:
    def __init__(
        self,
        thread_id: int,
        chunk: List[str],
        region_geofence: str,
        routing_type: Union[
            CatchmentAreaRoutingTypeActiveMobility, CatchmentAreaRoutingTypeCar
        ],
    ) -> None:
        self.thread_id: int = thread_id
        self.routing_network: Optional[Dict[str, Any]] = None  # TODO: Replace Any with more specific type
        self.chunk: List[str] = chunk
        self.region_geofence: str = region_geofence
        self.routing_type: Union[
            CatchmentAreaRoutingTypeActiveMobility, CatchmentAreaRoutingTypeCar
        ] = routing_type
        self.INSERT_BATCH_SIZE: int = 800
        self.matrix_resolution: int = MATRIX_RESOLUTION_CONFIG[routing_type.value]
        max_traveltime: float = ROUTING_COST_CONFIG[routing_type.value].max_traveltime
        if isinstance(routing_type, CatchmentAreaRoutingTypeActiveMobility):
            self.buffer_distance: float = max_traveltime * (
                (ROUTING_COST_CONFIG[routing_type.value].speed * 1000) / 60
            )
        else:
            self.buffer_distance: float = max_traveltime * (
                (settings.CATCHMENT_AREA_CAR_BUFFER_DEFAULT_SPEED * 1000) / 60
            )
        self.db_connection: Optional[AsyncSession] = None
        self.insert_string: str = ""
        self.num_rows_queued: int = 0

    async def generate_multi_catchment_area_request(
        self, h3_6_index: str
    ) -> Union[ICatchmentAreaActiveMobility, ICatchmentAreaCar]:
        """Produce a multi-catchment area request for a given H3_6 index and routing type."""
        if self.db_connection is None:
            raise ValueError("Database connection is not initialized")

        sql_get_centroid: Executable = text(f"""
            WITH centroid AS (
                SELECT ST_SetSRID(h3_cell_to_lat_lng(h3_index)::geometry, 4326) AS geom
                FROM h3_cell_to_children('{h3_6_index}'::h3index, {self.matrix_resolution}) AS h3_index
            )
            SELECT ST_X(geom), ST_Y(geom)
            FROM centroid;
        """)
        result_raw = await self.db_connection.execute(sql_get_centroid)
        result: List[Tuple[float, float]] = [tuple(row) for row in result_raw.fetchall()]

        origin_lat: List[float] = []
        origin_lng: List[float] = []
        for centroid in result:
            origin_lat.append(centroid[1])
            origin_lng.append(centroid[0])

        if isinstance(self.routing_type, CatchmentAreaRoutingTypeActiveMobility):
            return ICatchmentAreaActiveMobility(
                starting_points=CatchmentAreaStartingPoints(
                    latitude=origin_lat,
                    longitude=origin_lng,
                ),
                routing_type=self.routing_type,
                travel_cost=ROUTING_COST_CONFIG[self.routing_type.value],
                scenario_id=None,
                street_network=CatchmentAreaStreetNetwork(
                    edge_layer_project_id=settings.DEFAULT_STREET_NETWORK_EDGE_LAYER_PROJECT_ID,
                    node_layer_project_id=settings.DEFAULT_STREET_NETWORK_NODE_LAYER_PROJECT_ID,
                ),
                catchment_area_type=CatchmentAreaType.polygon,
                polygon_difference=True,
                result_table="",
                layer_id=None,
            )
        return ICatchmentAreaCar(
            starting_points=CatchmentAreaStartingPoints(
                latitude=origin_lat,
                longitude=origin_lng,
            ),
            routing_type=CatchmentAreaRoutingTypeCar.car,
            travel_cost=ROUTING_COST_CONFIG[self.routing_type.value],
            scenario_id=None,
            street_network=CatchmentAreaStreetNetwork(
                edge_layer_project_id=settings.DEFAULT_STREET_NETWORK_EDGE_LAYER_PROJECT_ID,
                node_layer_project_id=settings.DEFAULT_STREET_NETWORK_NODE_LAYER_PROJECT_ID,
            ),
            catchment_area_type=CatchmentAreaType.polygon,
            polygon_difference=True,
            result_table="",
            layer_id=None,
        )

    async def get_cell_grid(
        self, h3_6_index: str
    ) -> Tuple[list, np.ndarray, np.ndarray]:
        """For an origin H3_6 index, fetch a buffered grid of potentially accessible cells."""
        if self.db_connection is None:
            raise ValueError("Database connection is not initialized")

        sql_get_relevant_cells: Executable = text(f"""
            WITH cells AS (
                SELECT h3_grid_disk(origin_h3_index, radius.value) AS h3_index
                FROM h3_cell_to_center_child('{h3_6_index}'::h3index, {self.matrix_resolution}) AS origin_h3_index,
                LATERAL (SELECT (h3_get_hexagon_edge_length_avg(6, 'm') + {self.buffer_distance})::int AS dist) AS buffer,
                LATERAL (SELECT (buffer.dist / (h3_get_hexagon_edge_length_avg({self.matrix_resolution}, 'm') * 1.5)::int) AS value) AS radius
            )
            SELECT h3_index, ST_X(centroid), ST_Y(centroid)
            FROM cells,
            LATERAL (
                SELECT ST_Transform(ST_SetSRID(point::geometry, 4326), 3857) AS centroid
                FROM h3_cell_to_lat_lng(h3_index) AS point
            ) sub;
        """)
        result_raw = await self.db_connection.execute(sql_get_relevant_cells)
        result: List[Tuple[str, float, float]] = [tuple(row) for row in result_raw.fetchall()]

        h3_index: list = [r[0] for r in result]
        x_centroids: np.ndarray = np.empty(len(result), dtype=np.float64)
        y_centroids: np.ndarray = np.empty(len(result), dtype=np.float64)

        for i in range(len(result)):
            x_centroids[i] = result[i][1]
            y_centroids[i] = result[i][2]

        return h3_index, x_centroids, y_centroids

    def add_to_insert_string(
        self, orig_id: str, dest_id: List[str], costs: np.ndarray, orig_h3_3: str
    ) -> None:
        """Append latest results to the current insert batch."""
        cost_map: Dict[int, List[str]] = {}

        for i in range(len(dest_id)):
            if math.isnan(costs[i]) or int(costs[i]) == 0:
                continue
            cost: int = int(costs[i])
            if cost not in cost_map:
                cost_map[cost] = []
            cost_map[cost].append(dest_id[i])

        if 1 not in cost_map:
            cost_map[1] = [orig_id]
        elif orig_id not in cost_map[1]:
            cost_map[1].append(orig_id)

        for traveltime in cost_map:
            self.insert_string += f"""(
                '{orig_id}'::h3index,
                ARRAY{cost_map[traveltime]}::h3index[],
                {traveltime},
                '{orig_h3_3}'
            ),"""
            self.num_rows_queued += 1

    async def write_to_db(self) -> None:
        """Write the current insert batch to the database."""
        if self.db_connection is None:
            raise ValueError("Database connection is not initialized")

        sql_insert_into_table: Executable = text(f"""
            INSERT INTO basic.traveltime_matrix_{self.routing_type.value}_{settings.HEATMAP_MATRIX_DATE_SUFFIX} (
                orig_id, dest_id, traveltime, h3_3
            )
            VALUES {self.insert_string.rstrip(",")}
            ON CONFLICT (orig_id, traveltime, h3_3)
            DO UPDATE SET dest_id = EXCLUDED.dest_id;
        """)
        await self.db_connection.execute(sql_insert_into_table)
        await self.db_connection.commit()

    def run(self) -> None:
        event_loop: asyncio.AbstractEventLoop = asyncio.new_event_loop()
        asyncio.set_event_loop(event_loop)

        self.db_connection = async_session()
        crud_catchment_area: CRUDCatchmentArea = CRUDCatchmentArea(
            db_connection=self.db_connection,
            redis=None,
        )

        if self.routing_network is None:
            self.routing_network, _ = event_loop.run_until_complete(
                StreetNetworkUtil(self.db_connection).fetch(
                    edge_layer_id=settings.BASE_STREET_NETWORK,
                    node_layer_id=None,
                    region_geofence=self.region_geofence,
                )
            )

        for index in tqdm(
            range(len(self.chunk)), desc=f"Thread {self.thread_id}", unit=" cell"
        ):
            h3_6_index: str = self.chunk[index]

            catchment_area_request: Union[ICatchmentAreaActiveMobility, ICatchmentAreaCar] = event_loop.run_until_complete(
                self.generate_multi_catchment_area_request(h3_6_index)
            )

            input_table: Optional[str] = None
            sub_routing_network: Optional[Any] = None  # TODO: Replace with more specific type
            origin_connector_ids: Optional[List[int]] = None
            origin_point_cell_index: Optional[List[str]] = None
            origin_point_h3_3: Optional[List[str]] = None
            network_modifications_table: Optional[str] = None

            try:
                input_table, num_points = event_loop.run_until_complete(
                    crud_catchment_area.create_input_table(catchment_area_request)
                )
                (
                    sub_routing_network,
                    network_modifications_table,
                    origin_connector_ids,
                    origin_point_cell_index,
                    origin_point_h3_3,
                ) = event_loop.run_until_complete(
                    crud_catchment_area.read_network(
                        self.routing_network,  # type: ignore  # Known to be initialized now
                        catchment_area_request,
                        input_table,
                        num_points,
                        self.matrix_resolution,
                    )
                )
                event_loop.run_until_complete(
                    crud_catchment_area.drop_temp_tables(
                        input_table, network_modifications_table
                    )
                )
            except Exception as e:
                event_loop.run_until_complete(self.db_connection.rollback())  # type: ignore
                if isinstance(e, DisconnectedOriginError):
                    print_error(
                        f"Thread {self.thread_id}: Skipping {h3_6_index} due to disconnected origin. Starting points table: {input_table}"
                    )
                    continue
                elif isinstance(e, BufferExceedsNetworkError):
                    print_error(
                        f"Thread {self.thread_id}: Skipping {h3_6_index} due to buffer exceeding network. Starting points table: {input_table}"
                    )
                    continue
                else:
                    print_error(str(e))
                    print_error(
                        f"Thread {self.thread_id}: Error processing {h3_6_index}, exiting."
                    )
                    break

            if sub_routing_network is None or origin_connector_ids is None or origin_point_cell_index is None or origin_point_h3_3 is None:
                continue

            speed: Optional[float] = None
            if isinstance(catchment_area_request, ICatchmentAreaActiveMobility):
                speed = catchment_area_request.travel_cost.speed / 3.6

            zoom: int
            if isinstance(catchment_area_request, ICatchmentAreaActiveMobility):
                zoom = 12
            else:
                zoom = 10

            try:
                (
                    edges_source,
                    edges_target,
                    edges_cost,
                    edges_reverse_cost,
                    edges_length,
                    unordered_map,
                    node_coords,
                    extent,
                    geom_address,
                    geom_array,
                ) = prepare_network_isochrone(edge_network_input=sub_routing_network)

                adj_list: Dict[int, List[Tuple[int, float]]] = construct_adjacency_list_(
                    len(unordered_map),
                    edges_source,
                    edges_target,
                    edges_cost,
                    edges_reverse_cost,
                )

                start_vertices_ids: np.ndarray = np.array(
                    [unordered_map[v] for v in origin_connector_ids], dtype=np.int64
                )

                distances_list: List[np.ndarray] = dijkstra_h3(
                    start_vertices_ids,
                    adj_list,
                    catchment_area_request.travel_cost.max_traveltime,
                    False,
                )

                (h3_index, h3_centroid_x, h3_centroid_y) = event_loop.run_until_complete(
                    self.get_cell_grid(h3_6_index)
                )

                self.insert_string = ""
                self.num_rows_queued = 0

                for i in range(len(origin_point_cell_index)):
                    mapped_cost: np.ndarray = network_to_grid_h3(
                        extent=extent,
                        zoom=zoom,
                        edges_source=edges_source,
                        edges_target=edges_target,
                        edges_length=edges_length,
                        geom_address=geom_address,
                        geom_array=geom_array,
                        distances=distances_list[i],
                        node_coords=node_coords,
                        speed=speed,
                        max_traveltime=catchment_area_request.travel_cost.max_traveltime,
                        centroid_x=h3_centroid_x,
                        centroid_y=h3_centroid_y,
                        is_distance_based=False,
                    )

                    self.add_to_insert_string(
                        orig_id=str(origin_point_cell_index[i]),
                        dest_id=h3_index,
                        costs=mapped_cost,
                        orig_h3_3=str(origin_point_h3_3[i]),
                    )

                    if (
                        self.num_rows_queued >= self.INSERT_BATCH_SIZE
                        or i == len(origin_point_cell_index) - 1
                    ):
                        event_loop.run_until_complete(self.write_to_db())
                        self.insert_string = ""
                        self.num_rows_queued = 0
            except Exception as e:
                event_loop.run_until_complete(self.db_connection.rollback())  # type: ignore
                print_error(str(e))
                print_error(
                    f"Thread {self.thread_id}: Error processing {h3_6_index}, exiting."
                )
                break

        event_loop.run_until_complete(self.db_connection.close())  # type: ignore
        event_loop.close()
        print_info(f"Thread {self.thread_id} finished.")
