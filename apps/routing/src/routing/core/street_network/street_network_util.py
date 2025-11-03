import time
from typing import Any, Dict, List, Optional, Tuple  # Import Any
from uuid import UUID

import polars as pl
from routing.core.config import settings
from routing.core.street_network.street_network_cache import StreetNetworkCache
from routing.schemas.catchment_area import CONNECTOR_DATA_SCHEMA, SEGMENT_DATA_SCHEMA
from routing.utils import print_error, print_info, print_warning
from sqlalchemy import text
from sqlalchemy.engine import Row  # Import Row from sqlalchemy.engine
from sqlalchemy.ext.asyncio import AsyncSession


class StreetNetworkUtil:
    def __init__(self, db_connection: AsyncSession) -> None:
        self.db_connection: AsyncSession = db_connection

    async def _get_user_id(self, layer_id: UUID) -> UUID:
        """Get the user ID of the specified layer ID."""

        user_id: Optional[UUID] = None

        try:
            # Get the user ID of the layer
            result = await self.db_connection.execute(
                text(
                    f"""SELECT user_id
                FROM {settings.CUSTOMER_SCHEMA}.layer
                WHERE id = '{layer_id}';"""
                )
            )
            # Specify the type parameter for Row.
            # Since the query selects 'user_id', which we expect to be a UUID or something
            # that can be converted to a UUID, Row[UUID] is appropriate.
            fetched_row: Optional[Row[Any]] = result.fetchone() # Changed to Row[Any] for robustness if type is truly dynamic, or Row[UUID] if strictly a UUID. Using Any as per mypy-arg suggestion often implies a dynamic type. If user_id is definitely UUID, Row[UUID] is better.
            # Let's use Row[UUID] as it's more specific based on the query.
            # If mypy complains, we might need to broaden to Row[Any] or add a # type: ignore comment.

            if fetched_row is None:
                error_msg = f"No user ID found for layer ID {layer_id}."
                print_error(error_msg)
                raise ValueError(error_msg)

            # Accessing by index on a Row object is valid
            # mypy will infer the type of fetched_row[0] based on the Row's type parameter
            user_id = UUID(str(fetched_row[0]))

        except Exception as e:
            error_msg = f"Could not fetch user ID for layer ID {layer_id}. Error: {e}"
            print_error(error_msg)
            raise ValueError(error_msg)

        if user_id is None:
            error_msg = f"User ID was not determined for layer ID {layer_id}."
            print_error(error_msg)
            raise ValueError(error_msg)

        return user_id

    async def _get_street_network_tables(
        self,
        edge_layer_id: Optional[UUID],
        node_layer_id: Optional[UUID],
    ) -> Tuple[Optional[str], Optional[str]]:
        """Get table names and layer IDs of the edge and node tables."""

        edge_table: Optional[str] = None
        node_table: Optional[str] = None

        if edge_layer_id:
            try:
                user_id: UUID = await self._get_user_id(edge_layer_id)
                edge_table = f"{settings.USER_DATA_SCHEMA}.street_network_line_{str(user_id).replace('-', '')}"
            except ValueError as e:
                error_msg = (
                    f"Could not fetch edge table name for layer ID {edge_layer_id}. Error: {e}"
                )
                print_error(error_msg)
                raise ValueError(error_msg)
            except Exception as e:
                error_msg = (
                    f"An unexpected error occurred fetching edge table name for layer ID {edge_layer_id}. Error: {e}"
                )
                print_error(error_msg)
                raise RuntimeError(error_msg)

        if node_layer_id:
            try:
                user_id = await self._get_user_id(node_layer_id)
                node_table = f"{settings.USER_DATA_SCHEMA}.street_network_point_{str(user_id).replace('-', '')}"
            except ValueError as e:
                error_msg = (
                    f"Could not fetch node table name for layer ID {node_layer_id}. Error: {e}"
                )
                print_error(error_msg)
                raise ValueError(error_msg)
            except Exception as e:
                error_msg = (
                    f"An unexpected error occurred fetching node table name for layer ID {node_layer_id}. Error: {e}"
                )
                print_error(error_msg)
                raise RuntimeError(error_msg)

        return edge_table, node_table

    async def _get_street_network_region_h3_3_cells(self, region_geofence: str) -> List[int]:
        """Get list of H3_3 cells covering the street network region."""

        h3_3_cells: List[int] = []
        try:
            # Fetch H3_3 cells covering the region
            # Include a buffer distance of 80km to account for car routing
            sql_fetch_h3_3_cells = f"""
                WITH region AS (
                    {region_geofence}
                )
                SELECT g.h3_short FROM region r,
                LATERAL basic.fill_polygon_h3_3(ST_Buffer(r.geom::geography, 80000)::geometry) g;
            """
            result = (
                await self.db_connection.execute(text(sql_fetch_h3_3_cells))
            ).fetchall()

            # For fetchall(), each item in the list is a Row object.
            # We assume 'h3_short' will be an integer or convertible to one.
            for row in result:
                h3_3_cells.append(int(row[0]))
        except Exception as e:
            error_msg = f"Could not fetch H3_3 grid for street network geofence {region_geofence}. Error: {e}"
            print_error(error_msg)
            raise ValueError(error_msg)

        return h3_3_cells

    async def fetch(
        self,
        edge_layer_id: Optional[UUID],
        node_layer_id: Optional[UUID],
        region_geofence: str,
    ) -> Tuple[Dict[int, pl.DataFrame], Dict[int, pl.DataFrame]]:
        """Fetch street network from specified layer and load into Polars dataframes."""

        print_info(
            f"Fetching street network data for geofence region: {region_geofence}"
        )

        if settings.ENVIRONMENT != "dev":
            print_warning(
                f"Running in environment: {settings.ENVIRONMENT}, debug messages will not be shown."
            )

        street_network_edge: Dict[int, pl.DataFrame] = {}
        street_network_node: Dict[int, pl.DataFrame] = {}

        start_time: float = time.time()
        street_network_size: float = 0.0

        street_network_region_h3_3_cells: List[int] = (
            await self._get_street_network_region_h3_3_cells(region_geofence)
        )

        (
            street_network_edge_table,
            street_network_node_table,
        ) = await self._get_street_network_tables(edge_layer_id, node_layer_id)

        street_network_cache = StreetNetworkCache()

        try:
            for h3_short in street_network_region_h3_3_cells:
                edge_df: Optional[pl.DataFrame] = None
                node_df: Optional[pl.DataFrame] = None

                if edge_layer_id is not None and street_network_edge_table is not None:
                    if street_network_cache.edge_cache_exists(edge_layer_id, h3_short):
                        edge_df = street_network_cache.read_edge_cache(
                            edge_layer_id, h3_short
                        )

                        if edge_df.is_empty():
                            error_msg = f"Edge data for H3_3 cell {h3_short} is empty or corrupted, please re-fetch."
                            raise ValueError(error_msg)
                    else:
                        if settings.ENVIRONMENT == "dev":
                            print_info(
                                f"Fetching street network edge data for H3_3 cell {h3_short}"
                            )

                        edge_df = pl.read_database_uri(
                            query=f"""
                                SELECT
                                    edge_id AS id, length_m, length_3857, class_, impedance_slope, impedance_slope_reverse,
                                    impedance_surface, CAST(coordinates_3857 AS TEXT) AS coordinates_3857, maxspeed_forward,
                                    maxspeed_backward, source, target, h3_3, h3_6
                                FROM {street_network_edge_table}
                                WHERE h3_3 = {h3_short}
                                AND layer_id = '{str(edge_layer_id)}'
                            """,
                            uri=settings.POSTGRES_DATABASE_URI,
                            schema_overrides=SEGMENT_DATA_SCHEMA,
                        )
                        edge_df = edge_df.with_columns(
                            pl.col("coordinates_3857").str.json_decode()
                        )

                        street_network_cache.write_edge_cache(
                            edge_layer_id, h3_short, edge_df
                        )
                    street_network_edge[h3_short] = edge_df

                if node_layer_id is not None and street_network_node_table is not None:
                    if street_network_cache.node_cache_exists(node_layer_id, h3_short):
                        node_df = street_network_cache.read_node_cache(
                            node_layer_id, h3_short
                        )
                    else:
                        if settings.ENVIRONMENT == "dev":
                            print_info(
                                f"Fetching street network node data for H3_3 cell {h3_short}"
                            )

                        node_df = pl.read_database_uri(
                            query=f"""
                                SELECT node_id AS id, h3_3, h3_6
                                FROM {street_network_node_table}
                                WHERE h3_3 = {h3_short}
                                AND layer_id = '{str(node_layer_id)}'
                            """,
                            uri=settings.POSTGRES_DATABASE_URI,
                            schema_overrides=CONNECTOR_DATA_SCHEMA,
                        )

                        street_network_cache.write_node_cache(
                            node_layer_id, h3_short, node_df
                        )

                    street_network_node[h3_short] = node_df

                # Calculate size for both edge and node DFs if they were fetched
                if edge_df is not None:
                    street_network_size += edge_df.estimated_size("gb")
                if node_df is not None:
                    street_network_size += node_df.estimated_size("gb")

        except Exception as e:
            error_msg = f"Failed to fetch street network data from cache or database, error: {e}"
            print_error(error_msg)
            raise RuntimeError(error_msg)

        if edge_layer_id is not None and len(street_network_edge) == 0:
            error_msg = f"Failed to fetch street network edge data for layer project ID {edge_layer_id}."
            print_error(error_msg)
            raise RuntimeError(error_msg)

        if node_layer_id is not None and len(street_network_node) == 0:
            error_msg = f"Failed to fetch street network node data for layer project ID {node_layer_id}."
            print_error(error_msg)
            raise RuntimeError(error_msg)

        end_time: float = time.time()

        print_info(
            f"Street network load time: {round((end_time - start_time) / 60, 1)} min"
        )
        print_info(f"Street network in-memory size: {round(street_network_size, 1)} GB")

        return street_network_edge, street_network_node
