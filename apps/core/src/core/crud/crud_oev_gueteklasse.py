import json
from datetime import timedelta
from typing import Any, Dict
from uuid import UUID, uuid4

from fastapi import BackgroundTasks
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from core.core.config import settings
from core.core.job import job_init, job_log, run_background_or_immediately
from core.core.tool import CRUDToolBase
from core.crud.crud_catchment_area import (
    call_routing_endpoint,
    create_temp_isochrone_table,
)
from core.db.models.layer import FeatureGeometryType, ToolType
from core.endpoints.deps import get_http_client
from core.schemas.catchment_area import CatchmentAreaRoutingModeActiveMobility
from core.schemas.error import AreaSizeError
from core.schemas.job import JobStatusType
from core.schemas.layer import IFeatureLayerToolCreate, UserDataGeomType
from core.schemas.oev_gueteklasse import CatchmentType, IOevGueteklasse
from core.schemas.project import IFeatureStandardProjectRead, IFeatureToolProjectRead
from core.schemas.toolbox_base import DefaultResultLayerName, MaxFeaturePolygonArea
from core.utils import build_where_clause, format_value_null_sql


class CRUDOevGueteklasse(CRUDToolBase):
    """CRUD for OEV-Gueteklasse."""

    def __init__(
        self,
        job_id: UUID,
        background_tasks: BackgroundTasks,
        async_session: AsyncSession,
        user_id: UUID,
        project_id: UUID,
    ) -> None:
        super().__init__(job_id, background_tasks, async_session, user_id, project_id)
        self.table_stations = (
            f"{settings.USER_DATA_SCHEMA}.point_{str(self.user_id).replace('-', '')}"
        )
        self.table_oev_gueteklasse = (
            f"{settings.USER_DATA_SCHEMA}.polygon_{str(self.user_id).replace('-', '')}"
        )
        self.http_client = get_http_client()

    @job_log(job_step_name="station_category")
    async def get_oev_gueteklasse_station_category(
        self,
        params: IOevGueteklasse,
        reference_layer_project: IFeatureStandardProjectRead | IFeatureToolProjectRead,
        station_category_layer: IFeatureLayerToolCreate,
    ) -> Dict[str, Any]:
        """Get station category."""

        input_table = reference_layer_project.table_name
        where_query = build_where_clause([reference_layer_project.where_query])
        query = text(f"""
            INSERT INTO {self.table_stations}({', '.join(station_category_layer.attribute_mapping.keys())}, layer_id, geom)
            WITH child_stops AS (
                SELECT *
                FROM basic.count_public_transport_services_station (
                    '{input_table}',
                    {reference_layer_project.id},
                    '{settings.CUSTOMER_SCHEMA}',
                    {format_value_null_sql(params.scenario_id)},
                    :where_query,
                    '{str(timedelta(seconds=params.time_window.from_time))}',
                    '{str(timedelta(seconds=params.time_window.to_time))}',
                    {params.time_window.weekday_integer}
                )
            ),
            stations AS (
                SELECT stop_id, stop_name, (oev_gueteklasse ->> 'frequency')::float AS frequency,
                (oev_gueteklasse ->> '_class')::integer AS _class, '{str(station_category_layer.id)}'::uuid AS layer_id, geom AS geom
                FROM (
                    SELECT parent_station.stop_id, parent_station.stop_name, grouped.trip_cnt_list, parent_station.geom
                    FROM (
                        SELECT parent_station, array_agg(trip_cnt) AS trip_cnt_list
                        FROM child_stops
                        WHERE parent_station IS NOT NULL
                        GROUP BY parent_station
                    ) grouped,
                    basic.stops parent_station
                    WHERE parent_station.stop_id = grouped.parent_station
                    UNION ALL
                    SELECT stop_id, stop_name, ARRAY[trip_cnt] AS trip_cnt_list, geom
                    FROM child_stops
                    WHERE parent_station IS NULL
                ) services_count,
                LATERAL basic.oev_guetklasse_station_category(
                    trip_cnt_list,
                    '{json.dumps(params.station_config.dict())}'::jsonb,
                    {params.time_window.from_time},
                    {params.time_window.to_time}
                ) oev_gueteklasse
            )
            SELECT *
            FROM stations;
        """)
        await self.async_session.execute(query, {"where_query": where_query})
        await self.async_session.commit()
        return {
            "status": JobStatusType.finished.value,
            "msg": "Station category created.",
        }

    async def create_difference_between_steps(
        self, temp_table_name: str, layer_id: UUID
    ) -> None:
        # Create difference between different buffers*
        await self.async_session.execute(
            text(f"""
            INSERT INTO {self.table_oev_gueteklasse} (text_attr1, integer_attr1, layer_id, geom)
            SELECT UPPER(CHR(a.pt_class + 96))::text, a.pt_class, '{layer_id}', CASE WHEN j.geom IS NULL THEN a.geom ELSE j.geom END AS geom
            FROM {temp_table_name} a
            LEFT JOIN LATERAL
            (
                SELECT ST_DIFFERENCE(a.geom, c.geom) AS geom
                FROM (
                    SELECT ST_UNION(b.geom) geom
                    FROM {temp_table_name} b
                    WHERE a.pt_class > b.pt_class
                    AND ST_Intersects(a.geom, b.geom)
                ) c
            ) j ON TRUE;
            """)
        )

    @job_log(job_step_name="station_buffer")
    async def compute_station_buffer(
        self,
        station_category_layer: IFeatureLayerToolCreate,
        catchment_layer: IFeatureLayerToolCreate,
        station_config: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Compute station buffer."""

        # Create temp table names
        table_suffix = str(self.job_id).replace("-", "")
        temp_buffered_stations = f"temporal.temp_buffered_stations_{table_suffix}"
        temp_union_buffer = f"temporal.temp_union_buffered_stations_{table_suffix}"

        # Create temp distributed table for buffered stations
        await self.async_session.execute(
            text(f"DROP TABLE IF EXISTS {temp_buffered_stations};")
        )
        await self.async_session.execute(
            text(f"""
            CREATE TABLE {temp_buffered_stations}
            (
                stop_id TEXT,
                pt_class integer,
                distance integer,
                geom geometry,
                h3_3 integer
            )
        """)
        )
        await self.async_session.execute(
            text(f"SELECT create_distributed_table('{temp_buffered_stations}', 'h3_3')")
        )

        # Buffer the stations in their respective intervals
        await self.async_session.execute(
            text(f"""INSERT INTO {temp_buffered_stations}
            SELECT text_attr1 AS stop_id,  REPLACE(j.value::TEXT, '"', '')::integer AS pt_class,
            j.KEY::integer distance, ST_BUFFER(s.geom::geography, j.KEY::integer)::geometry AS geom,
            basic.to_short_h3_3(h3_lat_lng_to_cell(geom::point, 3)::bigint)
            FROM {self.table_stations} s
            , LATERAL jsonb_each('{json.dumps(station_config)}'::jsonb -> 'classification' -> s.integer_attr1::text) j
            WHERE layer_id = '{station_category_layer.id}';
            """)
        )
        await self.async_session.execute(
            text(
                f"""CREATE INDEX ON {temp_buffered_stations} USING GIST(h3_3, geom);"""
            )
        )

        # Union the buffers. It is not made use of citus distribution column here as it is a challenge to group over shards efficiently.
        await self.async_session.execute(
            text(f"DROP TABLE IF EXISTS {temp_union_buffer};")
        )
        await self.async_session.execute(
            text(f"""CREATE TABLE {temp_union_buffer} AS
            WITH clustered_buffer AS
            (
                SELECT s.geom, s.pt_class,
                ST_ClusterDBSCAN(geom, eps := 0, minpoints := 1) OVER (PARTITION BY pt_class) AS cluster_id
                FROM {temp_buffered_stations} s
            )
            SELECT b.pt_class, b.geom
            FROM clustered_buffer b
            WHERE cluster_id IS NULL
            UNION ALL
            SELECT b.pt_class, ST_UNION(b.geom) AS geom
            FROM clustered_buffer b
            WHERE cluster_id IS NOT NULL
            GROUP BY b.pt_class, cluster_id;""")
        )
        await self.async_session.execute(
            text(f"""CREATE INDEX ON {temp_union_buffer} USING GIST(geom);""")
        )
        # Create difference between different buffers*
        await self.create_difference_between_steps(
            temp_union_buffer, catchment_layer.id
        )

        # Delete temporary tables
        await self.delete_temp_tables()

        return {
            "status": JobStatusType.finished.value,
            "msg": "Station buffers are created.",
        }

    @job_log(job_step_name="station_buffer")
    async def compute_station_network_catchment(
        self,
        station_category_layer: IFeatureLayerToolCreate,
        catchment_layer: IFeatureLayerToolCreate,
        station_config: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Compute station network catchment."""

        if not self.job_id:
            raise ValueError("Job ID not defined")

        # Create temp table names
        table_suffix = str(self.job_id).replace("-", "")
        temp_catchment_stations = f"temporal.temp_catchment_stations_{table_suffix}"
        temp_union_catchment = f"temporal.temp_union_catchment_{table_suffix}"
        sql_create_temp_catchment_stations = text(f"""
            CREATE TABLE {temp_catchment_stations}
            (
                pt_class integer,
                distance integer,
                geom geometry
            );
        """)
        await self.async_session.execute(
            text(f"DROP TABLE IF EXISTS {temp_catchment_stations};")
        )
        await self.async_session.execute(sql_create_temp_catchment_stations)

        # Calculate catchment areas for each pt class
        for pt_class in station_config["classification"]:
            classification = station_config["classification"][pt_class]
            # Create temp table for isochrones
            temp_batch_catchment_table = await create_temp_isochrone_table(
                async_session=self.async_session, job_id=self.job_id
            )

            # Get max distance from station_config
            max_distance = max(int(key) for key in classification.keys())

            # Get lats and lons from self.table_stations
            query = text(f"""
                SELECT ARRAY_AGG(ST_X(geom)) AS lons, ARRAY_AGG(ST_Y(geom)) AS lats
                FROM {self.table_stations}
                WHERE layer_id = '{station_category_layer.id}'
                AND integer_attr1 = {pt_class};
            """)
            starting_points = (await self.async_session.execute(query)).fetchall()

            lons = starting_points[0][0]
            lats = starting_points[0][1]

            # Get step count by dividing max_distance by 50
            steps = int(max_distance / 50)

            if lats is not None and lons is not None:
                # Construct request payload
                request_payload = {
                    "starting_points": {
                        "latitude": lats,
                        "longitude": lons,
                    },
                    "routing_type": CatchmentAreaRoutingModeActiveMobility.walking,
                    "travel_cost": {
                        "max_distance": max_distance,
                        "steps": steps,
                    },
                    "catchment_area_type": "polygon",
                    "polygon_difference": False,
                    "result_table": temp_batch_catchment_table,
                    "layer_id": str(uuid4()),
                }
                # Call routing endpoint
                await call_routing_endpoint(
                    CatchmentAreaRoutingModeActiveMobility.walking,
                    request_payload,
                    self.http_client,
                )

                # Insert into temp_catchment_stations
                await self.async_session.execute(
                    text(f"""
                    INSERT INTO {temp_catchment_stations}
                    SELECT ('{json.dumps(classification)}'::jsonb ->> integer_attr1::TEXT)::integer, integer_attr1 AS distance, geom
                    FROM {temp_batch_catchment_table}
                    WHERE '{json.dumps(classification)}'::jsonb ->> integer_attr1::TEXT IS NOT NULL
                    """)
                )

                await self.async_session.commit()

        # Union the catchments by pt_class and isnert into user table
        sql_union = text(f"""
            CREATE TABLE {temp_union_catchment} AS
            SELECT a.pt_class, '{catchment_layer.id}', ST_UNION(a.geom) AS geom
            FROM {temp_catchment_stations} a
            GROUP BY a.pt_class;
        """)
        await self.async_session.execute(sql_union)
        await self.async_session.commit()

        # Create difference between different catchments
        await self.create_difference_between_steps(
            temp_union_catchment, catchment_layer.id
        )

        # Delete temporary tables
        await self.delete_temp_tables()

        return {
            "status": JobStatusType.finished.value,
            "msg": "Station network catchment created.",
        }

    @run_background_or_immediately(settings)
    @job_init()
    async def oev_gueteklasse_run(self, params: IOevGueteklasse) -> Dict[str, Any]:
        """Compute ÖV-Güteklassen."""

        if not self.job_id:
            raise ValueError("Job ID not defined")

        # Check if reference layer qualifies for ÖV-Güteklassen
        layer_project = await self.get_layers_project(
            params=params,
        )
        reference_layer_project = layer_project["reference_area_layer_project_id"]

        # Check size again in case of network catchment
        if params.catchment_type == CatchmentType.network:
            # Check reference area size
            area = await self.check_reference_area_size(
                layer_project=reference_layer_project,
                tool_type=params.tool_type,
            )
            # Make sure in case of network catchment that the max size is only 10% of the default max size.
            if area > MaxFeaturePolygonArea[ToolType.oev_gueteklasse.value].value / 10:
                raise AreaSizeError(
                    f"The operation cannot be performed on more than {MaxFeaturePolygonArea[ToolType.oev_gueteklasse.value].value} km2."
                )

        # Create layer object
        station_category_layer = IFeatureLayerToolCreate(
            name=DefaultResultLayerName.oev_gueteklasse_station.value,
            feature_layer_geometry_type=FeatureGeometryType[
                UserDataGeomType.point.value
            ],
            attribute_mapping={
                "text_attr1": "stop_id",
                "text_attr2": "stop_name",
                "float_attr1": "frequency",
                "integer_attr1": "station_category",
            },
            tool_type=params.tool_type.value,
            job_id=self.job_id,
        )

        # Get station category
        await self.get_oev_gueteklasse_station_category(
            params=params,
            reference_layer_project=reference_layer_project,
            station_category_layer=station_category_layer,
        )

        # Create layer for buffer results
        catchment_layer = IFeatureLayerToolCreate(
            name=DefaultResultLayerName.oev_gueteklasse.value,
            feature_layer_geometry_type=FeatureGeometryType[
                UserDataGeomType.polygon.value
            ],
            attribute_mapping={
                "text_attr1": "pt_class",
                "integer_attr1": "pt_class_number",
            },
            tool_type=ToolType.oev_gueteklasse,
            job_id=self.job_id,
        )

        # Compute station buffer
        if params.catchment_type == CatchmentType.buffer:
            await self.compute_station_buffer(
                station_category_layer=station_category_layer,
                catchment_layer=catchment_layer,
                station_config=params.station_config.dict(),
            )
        elif params.catchment_type == CatchmentType.network:
            await self.compute_station_network_catchment(
                station_category_layer=station_category_layer,
                catchment_layer=catchment_layer,
                station_config=params.station_config.dict(),
            )

        # Create result layers
        await self.create_feature_layer_tool(
            layer_in=catchment_layer,
            params=params,
        )
        await self.create_feature_layer_tool(
            layer_in=station_category_layer,
            params=params,
        )
        return {
            "status": JobStatusType.finished.value,
            "msg": "ÖV-Güteklassen created.",
        }
