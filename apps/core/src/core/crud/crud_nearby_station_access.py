import json
from datetime import timedelta
from typing import Any, Dict
from uuid import UUID

from fastapi import BackgroundTasks
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from core.core.config import settings
from core.core.job import job_init, job_log, run_background_or_immediately
from core.core.tool import CRUDToolBase
from core.crud.crud_catchment_area import CRUDCatchmentAreaActiveMobility
from core.db.models.layer import FeatureGeometryType
from core.endpoints.deps import get_http_client
from core.schemas.catchment_area import (
    CatchmentAreaNearbyStationAccess,
    CatchmentAreaTravelTimeCostActiveMobility,
    CatchmentAreaTypeActiveMobility,
)
from core.schemas.error import SQLError
from core.schemas.job import JobStatusType
from core.schemas.layer import IFeatureLayerToolCreate, UserDataGeomType
from core.schemas.nearby_station_access import INearbyStationAccess
from core.schemas.toolbox_base import DefaultResultLayerName
from core.schemas.trip_count_station import public_transport_types


class CRUDNearbyStationAccess(CRUDToolBase):
    """CRUD for Nearby Station Access."""

    def __init__(
        self,
        job_id: UUID,
        background_tasks: BackgroundTasks,
        async_session: AsyncSession,
        user_id: UUID,
        project_id: UUID,
    ) -> None:
        super().__init__(job_id, background_tasks, async_session, user_id, project_id)
        self.result_table = (
            f"{settings.USER_DATA_SCHEMA}.point_{str(self.user_id).replace('-', '')}"
        )

    @job_log(job_step_name="nearby_station_access")
    async def nearby_station_access(
        self, params: INearbyStationAccess
    ) -> Dict[str, Any]:
        """Computes a catchment area based on provided parameters, then identifies stations within this catchment area
        and computes the frequency of public transport routes serving these stations."""

        if not self.job_id:
            raise ValueError("Job ID not defined")

        # Create feature layer to store computed nearby stations output
        layer_stations = IFeatureLayerToolCreate(
            name=DefaultResultLayerName.nearby_station_access.value,
            feature_layer_geometry_type=FeatureGeometryType[
                UserDataGeomType.point.value
            ],
            attribute_mapping={
                "text_attr1": "stop_name",
                "text_attr2": "dominant_mode",
                "integer_attr1": "access_time",
                "integer_attr2": "agg_frequency",
                "jsonb_attr1": "routes",
            },
            tool_type=params.tool_type.value,
            job_id=self.job_id,
        )
        result_table = f"{settings.USER_DATA_SCHEMA}.{layer_stations.feature_layer_geometry_type.value}_{str(self.user_id).replace('-', '')}"

        try:
            # Create result table to store catchment area geometry
            catchment_area_table = f"temporal.temp_{str(self.job_id).replace('-', '')}"
            sql_create_temp_table = text(f"""
                CREATE TABLE {catchment_area_table} (
                    id serial,
                    layer_id text,
                    geom geometry,
                    integer_attr1 smallint
                );
            """)
            await self.async_session.execute(sql_create_temp_table)
            await self.async_session.commit()
        except Exception as e:
            await self.async_session.rollback()
            raise SQLError(e)

        # Create active mobility catchment area request payload
        catchment_area_request = CatchmentAreaNearbyStationAccess(
            starting_points=params.starting_points,
            routing_type=params.access_mode,
            travel_cost=CatchmentAreaTravelTimeCostActiveMobility(
                max_traveltime=params.max_traveltime,
                steps=params.max_traveltime,
                speed=params.speed,
            ),
            catchment_area_type=CatchmentAreaTypeActiveMobility.polygon,
            polygon_difference=True,
            scenario_id=params.scenario_id,
            street_network=params.street_network,
        )

        # Compute catchment area
        await CRUDCatchmentAreaActiveMobility(
            job_id=self.job_id,
            background_tasks=self.background_tasks,
            async_session=self.async_session,
            user_id=self.user_id,
            project_id=self.project_id,
            http_client=get_http_client(),
        ).catchment_area(
            params=catchment_area_request,
            result_params={
                "result_table": catchment_area_table,
                "layer_id": str(layer_stations.id),
                "starting_points_layer_name": DefaultResultLayerName.nearby_station_access_starting_points,
            },
        )

        # Create mapping for transport modes
        flat_mode_mapping = {}
        for outer_key, inner_dict in public_transport_types.items():
            for inner_key in inner_dict:
                flat_mode_mapping[str(inner_key)] = outer_key

        modes_sql_array = (
            "{" + ",".join(f'"{mode.value}"' for mode in params.mode) + "}"
        )

        # Run query to find nearby stations, compute route frequencies and insert into result table
        sql_compute_nearby_station_access = text(f"""
            WITH stop AS (
                SELECT stop_id, stop_name, access_time, geom, h3_3, unpacked.KEY AS route_type, unpacked.value AS routes
                FROM basic.station_route_count(
                    '{catchment_area_table}',
                    '',
                    '{str(timedelta(seconds=params.time_window.from_time))}'::interval,
                    '{str(timedelta(seconds=params.time_window.to_time))}'::interval,
                    {params.time_window.weekday_integer}
                ),
                LATERAL jsonb_each(route_ids) unpacked
            ),
            service AS (
                SELECT sr.stop_id, sr.stop_name, sr.access_time, sr.geom, sr.route_id, sr.route_type, sr.mode, count(sr.route_id) AS trip_cnt
                FROM (
                    SELECT stop_id, stop_name, access_time, geom, route_type, jsonb_array_elements_text(routes) as route_id,
                        ('{json.dumps(flat_mode_mapping)}'::JSONB ->> route_type) AS mode
                    FROM stop
                ) sr
                WHERE sr.mode = ANY('{modes_sql_array}'::text[])
                GROUP BY sr.stop_id, sr.stop_name, sr.access_time, sr.geom, sr.route_id, sr.route_type, sr.mode
            ),
            frequency AS (
                SELECT s.stop_id, s.stop_name, s.access_time, s.geom, r.route_short_name,
                    s.route_type, s.mode, trip_cnt, ROUND({params.time_window.duration_minutes} / trip_cnt) AS frequency
                FROM service s
                INNER JOIN basic.routes r ON r.route_id = s.route_id
            )
            INSERT INTO {result_table} (layer_id, geom, text_attr1, text_attr2, integer_attr1, integer_attr2, jsonb_attr1)
            SELECT *
            FROM
            (
                SELECT '{str(layer_stations.id)}'::uuid, geom, stop_name, dominant_mode.*, access_time, agg_frequency, routes
                FROM (
                    SELECT geom, stop_name, access_time, ROUND(120 / sum(trip_cnt)) AS agg_frequency,
                    array_agg(DISTINCT route_type) AS route_types,
                    jsonb_agg(jsonb_build_object('route_name', route_short_name, 'mode', mode, 'frequency', frequency)) AS routes
                    FROM frequency
                    GROUP BY stop_id, stop_name, access_time, geom
                ) sub,
                LATERAL basic.identify_dominant_mode(route_types, '{json.dumps(flat_mode_mapping)}'::JSONB) dominant_mode
            ) x
            ORDER BY access_time
        """)
        try:
            await self.async_session.execute(sql_compute_nearby_station_access)
            await self.async_session.commit()
        except Exception as e:
            await self.async_session.rollback()
            raise SQLError(e)

        try:
            # Delete temporary catchment area result table
            await self.async_session.execute(
                text(f"DROP TABLE IF EXISTS {catchment_area_table};")
            )
        except Exception as e:
            await self.async_session.rollback()
            raise SQLError(e)

        await self.create_feature_layer_tool(
            layer_in=layer_stations,
            params=params,
        )

        # TODO: Return the job id.
        # TO BE DISCUSSED: For the tests we should consider mocking the catchment area request as otherswise it is very hard to test the catchment area in isolation.
        return {
            "status": JobStatusType.finished.value,
            "msg": "Nearby station access created.",
        }

    @run_background_or_immediately(settings)
    @job_init()
    async def nearby_station_access_run(
        self, params: INearbyStationAccess
    ) -> Dict[str, Any]:
        return await self.nearby_station_access(params=params)
