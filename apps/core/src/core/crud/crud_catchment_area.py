import asyncio
from typing import Any, Dict
from uuid import UUID

from fastapi import BackgroundTasks
from httpx import AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from core.core.config import settings
from core.core.job import job_init, job_log, run_background_or_immediately
from core.core.tool import CRUDToolBase
from core.jsoline import generate_jsolines
from core.schemas.catchment_area import (
    CatchmentAreaNearbyStationAccess,
    CatchmentAreaRoutingModeActiveMobility,
    CatchmentAreaRoutingModeCar,
    CatchmentAreaTravelTimeCostActiveMobility,
    CatchmentAreaTravelTimeCostMotorizedMobility,
    CatchmentAreaTypePT,
    ICatchmentAreaActiveMobility,
    ICatchmentAreaCar,
    ICatchmentAreaPT,
)
from core.schemas.error import (
    OutOfGeofenceError,
    R5CatchmentAreaComputeError,
    R5EndpointError,
    RoutingEndpointError,
    SQLError,
)
from core.schemas.job import JobStatusType
from core.schemas.layer import FeatureGeometryType, IFeatureLayerToolCreate
from core.schemas.toolbox_base import (
    CatchmentAreaGeometryTypeMapping,
    DefaultResultLayerName,
)
from core.utils import decode_r5_grid, format_value_null_sql


async def call_routing_endpoint(
    routing_mode: CatchmentAreaRoutingModeActiveMobility | CatchmentAreaRoutingModeCar,
    request_payload: dict,
    http_client: AsyncClient,
) -> None:
    try:
        # Call GOAT Routing endpoint multiple times for upto 20 seconds / 10 retries
        for i in range(settings.CRUD_NUM_RETRIES):
            # Call GOAT Routing endpoint to compute catchment area
            url = (
                f"{settings.GOAT_ROUTING_URL}/active-mobility/catchment-area"
                if type(routing_mode) is CatchmentAreaRoutingModeActiveMobility
                else f"{settings.GOAT_ROUTING_URL}/motorized-mobility/catchment-area"
            )
            response = await http_client.post(
                url=url,
                json=request_payload,
                headers={"Authorization": settings.GOAT_ROUTING_AUTHORIZATION},
            )
            if response.status_code == 202:
                # Endpoint is still processing request, retry shortly
                if i == settings.CRUD_NUM_RETRIES - 1:
                    raise Exception(
                        "GOAT routing endpoint took too long to process request."
                    )
                await asyncio.sleep(settings.CRUD_RETRY_INTERVAL)
                continue
            elif response.status_code == 201:
                # Endpoint has finished processing request, break
                break
            else:
                raise Exception(response.text)
    except Exception as e:
        raise RoutingEndpointError(
            f"Error while calling the routing endpoint: {str(e)}"
        )


async def create_temp_isochrone_table(async_session: AsyncSession, job_id: UUID) -> str:
    try:
        # Create result table to store catchment area geometry
        catchment_area_table = f"temporal.temp_{str(job_id).replace('-', '')}"
        # Drop table if exists
        sql_drop_temp_table = text(f"""
            DROP TABLE IF EXISTS {catchment_area_table};
        """)
        await async_session.execute(sql_drop_temp_table)
        sql_create_temp_table = text(f"""
            CREATE TABLE {catchment_area_table} (
                id serial,
                layer_id text,
                geom geometry,
                integer_attr1 smallint
            );
        """)
        await async_session.execute(sql_create_temp_table)
        await async_session.commit()
    except Exception as e:
        await async_session.rollback()
        raise SQLError(e)

    return catchment_area_table


class CRUDCatchmentAreaBase(CRUDToolBase):
    def __init__(
        self,
        job_id: UUID,
        background_tasks: BackgroundTasks,
        async_session: AsyncSession,
        user_id: UUID,
        project_id: UUID,
    ) -> None:
        super().__init__(job_id, background_tasks, async_session, user_id, project_id)
        self.table_starting_points = (
            f"{settings.USER_DATA_SCHEMA}.point_{str(self.user_id).replace('-', '')}"
        )

    async def create_layer_starting_points(
        self,
        layer_name: DefaultResultLayerName,
        params: (
            ICatchmentAreaActiveMobility
            | ICatchmentAreaCar
            | ICatchmentAreaPT
            | CatchmentAreaNearbyStationAccess
        ),
    ) -> IFeatureLayerToolCreate:
        if not self.job_id:
            raise ValueError("Job ID not defined")

        # Create layer object
        layer = IFeatureLayerToolCreate(
            name=layer_name.value,
            feature_layer_geometry_type=FeatureGeometryType.point,
            attribute_mapping={},
            tool_type=params.tool_type.value,
            job_id=self.job_id,
        )

        # Check if starting points are within the geofence
        for i in range(0, len(params.starting_points.latitude), 500):
            # Create insert query
            lats = params.starting_points.latitude[i : i + 500]
            lons = params.starting_points.longitude[i : i + 500]
            sql = text(f"""
                WITH to_test AS
                (
                    SELECT ST_SETSRID(ST_MAKEPOINT(lon[gs], lat[gs]), 4326) AS geom
                    FROM generate_series(1, array_length(ARRAY{str(lats)}, 1)) AS gs,
                    LATERAL (SELECT ARRAY{str(lats)} AS lat, ARRAY{str(lons)} AS lon) AS arrays
                )
                SELECT COUNT(*)
                FROM to_test t
                WHERE NOT EXISTS (
                    SELECT 1
                    FROM {params.geofence_table} AS g
                    WHERE ST_INTERSECTS(t.geom, g.geom)
                )
            """)
            # Execute query
            cnt_not_intersecting = (
                (await self.async_session.execute(sql)).scalars().first()
            )
            assert cnt_not_intersecting is not None

            if cnt_not_intersecting > 0:
                raise OutOfGeofenceError(
                    f"There are {cnt_not_intersecting} starting points that are not within the geofence. Please check your starting points."
                )

        # Save data into user data tables in batches of 500
        for i in range(0, len(params.starting_points.latitude), 500):
            # Create insert query
            lats = params.starting_points.latitude[i : i + 500]
            lons = params.starting_points.longitude[i : i + 500]
            sql = text(f"""
                INSERT INTO {self.table_starting_points} (layer_id, geom)
                SELECT '{layer.id}', ST_SETSRID(ST_MAKEPOINT(lon[gs], lat[gs]), 4326) AS geom
                FROM generate_series(1, array_length(ARRAY{str(lats)}, 1)) AS gs,
                LATERAL (SELECT ARRAY{str(lats)} AS lat, ARRAY{str(lons)} AS lon) AS arrays
            """)
            # Execute query
            await self.async_session.execute(sql)

        return layer

    async def get_lats_lons(
        self,
        layer_name: DefaultResultLayerName,
        params: (
            ICatchmentAreaActiveMobility
            | ICatchmentAreaCar
            | ICatchmentAreaPT
            | CatchmentAreaNearbyStationAccess
        ),
    ) -> Dict[str, Any]:
        # Check if starting points are a layer else create layer
        if params.starting_points.layer_project_id:
            layer_starting_points = await self.get_layers_project(params)
            where_query = layer_starting_points["layer_project_id"].where_query
            table_name = layer_starting_points["layer_project_id"].table_name
        else:
            layer_starting_points = await self.create_layer_starting_points(
                layer_name=layer_name, params=params
            )
            where_query = f"layer_id = '{layer_starting_points.id}'"
            table_name = self.table_starting_points

        # Fetch features from input layer while applying a scenario if specified
        layer_project_id = (
            "NULL"
            if params.starting_points.layer_project_id is None
            else f"{params.starting_points.layer_project_id}"
        )
        sql = text(f"""
            SELECT ST_X(geom) AS lon, ST_Y(geom) AS lat
            FROM (
                WITH scenario_features AS (
                    SELECT sf.feature_id AS id, sf.geom, sf.edit_type
                    FROM {settings.CUSTOMER_SCHEMA}.scenario_scenario_feature ssf
                    INNER JOIN {settings.CUSTOMER_SCHEMA}.scenario_feature sf ON sf.id = ssf.scenario_feature_id
                    WHERE ssf.scenario_id = {format_value_null_sql(params.scenario_id)}
                    AND sf.layer_project_id = {layer_project_id}
                )
                    SELECT original_features.id, original_features.geom
                    FROM (SELECT * FROM {table_name} WHERE {where_query}) original_features
                    LEFT JOIN scenario_features ON original_features.id = scenario_features.id
                    WHERE scenario_features.id IS NULL
                UNION ALL
                    SELECT scenario_features.id, scenario_features.geom
                    FROM scenario_features
                    WHERE edit_type IN ('n', 'm')
            ) input_features;
        """)
        starting_points = (await self.async_session.execute(sql)).mappings().fetchall()
        starting_points = [dict(x) for x in starting_points]
        lats = [x["lat"] for x in starting_points]
        lons = [x["lon"] for x in starting_points]
        return {
            "layer_starting_points": layer_starting_points,
            "lats": lats,
            "lons": lons,
        }


class CRUDCatchmentAreaActiveMobility(CRUDCatchmentAreaBase):
    def __init__(
        self,
        job_id: UUID,
        background_tasks: BackgroundTasks,
        async_session: AsyncSession,
        user_id: UUID,
        project_id: UUID,
        http_client: AsyncClient,
    ) -> None:
        super().__init__(job_id, background_tasks, async_session, user_id, project_id)

        self.http_client = http_client

    async def catchment_area(
        self,
        params: ICatchmentAreaActiveMobility | CatchmentAreaNearbyStationAccess,
        result_params: Dict[str, Any] | None = None,
    ) -> Dict[str, Any]:
        """Compute active mobility catchment area using GOAT Routing endpoint."""

        if not self.job_id:
            raise ValueError("Job ID not defined")

        # Fetch starting points
        starting_points = await self.get_lats_lons(
            layer_name=(
                DefaultResultLayerName.catchment_area_starting_points
                if not result_params
                else result_params["starting_points_layer_name"]
            ),
            params=params,
        )
        lats = starting_points["lats"]
        lons = starting_points["lons"]
        layer_starting_points = starting_points["layer_starting_points"]

        if not result_params:
            # Create feature layer to store computed catchment area output
            layer_catchment_area = IFeatureLayerToolCreate(
                name=DefaultResultLayerName.catchment_area_active_mobility.value,
                feature_layer_geometry_type=FeatureGeometryType[
                    CatchmentAreaGeometryTypeMapping[params.catchment_area_type.value]
                ],
                attribute_mapping={"integer_attr1": "travel_cost"},
                tool_type=params.tool_type.value,
                job_id=self.job_id,
            )
            result_table = f"{settings.USER_DATA_SCHEMA}.{layer_catchment_area.feature_layer_geometry_type.value}_{str(self.user_id).replace('-', '')}"
            layer_id = layer_catchment_area.id
        else:
            layer_id = result_params["layer_id"]

        # Construct request payload
        request_payload = {
            "starting_points": {
                "latitude": lats,
                "longitude": lons,
            },
            "routing_type": params.routing_type.value,
            "travel_cost": (
                {
                    "max_traveltime": params.travel_cost.max_traveltime,
                    "steps": params.travel_cost.steps,
                    "speed": params.travel_cost.speed,
                }
                if type(params.travel_cost) is CatchmentAreaTravelTimeCostActiveMobility
                else {
                    "max_distance": params.travel_cost.max_distance,
                    "steps": params.travel_cost.steps,
                }
            ),
            "catchment_area_type": params.catchment_area_type.value,
            "polygon_difference": params.polygon_difference,
            "result_table": (
                result_table if not result_params else result_params["result_table"]
            ),
            "layer_id": str(layer_id),
        }

        # Append scenario ID if specified
        if params.scenario_id:
            request_payload["scenario_id"] = str(params.scenario_id)

        # Append street network config if specified
        if params.street_network:
            request_payload["street_network"] = {
                "edge_layer_project_id": params.street_network.edge_layer_project_id,
                "node_layer_project_id": params.street_network.node_layer_project_id,
            }

        await call_routing_endpoint(
            params.routing_type, request_payload, self.http_client
        )

        # Create layers only if result_params are not provided
        if not result_params:
            # Create new layers.
            await self.create_feature_layer_tool(
                layer_in=layer_catchment_area,
                params=params,
            )

        # Create new layer if starting points are not a layer
        if not params.starting_points.layer_project_id:
            await self.create_feature_layer_tool(
                layer_in=layer_starting_points,
                params=params,
            )

        return {
            "status": JobStatusType.finished.value,
            "msg": "Active mobility catchment area was successfully computed.",
        }

    @job_log(job_step_name="catchment_area")
    async def catchment_area_job(
        self, params: ICatchmentAreaActiveMobility
    ) -> Dict[str, Any]:
        return await self.catchment_area(params=params)

    @run_background_or_immediately(settings)
    @job_init()
    async def run_catchment_area(
        self, params: ICatchmentAreaActiveMobility
    ) -> Dict[str, Any]:
        return await self.catchment_area_job(params=params)


class CRUDCatchmentAreaPT(CRUDCatchmentAreaBase):
    def __init__(
        self,
        job_id: UUID,
        background_tasks: BackgroundTasks,
        async_session: AsyncSession,
        user_id: UUID,
        project_id: UUID,
        http_client: AsyncClient,
    ) -> None:
        super().__init__(job_id, background_tasks, async_session, user_id, project_id)

        self.http_client = http_client

    async def write_catchment_area_result(
        self,
        catchment_area_type: CatchmentAreaTypePT,
        layer_id: UUID,
        result_table: str,
        shapes: Dict[str, Any],
        grid: Any,
        polygon_difference: bool,
    ) -> None:
        """Save the result of the catchment area computation to the database."""

        if catchment_area_type == "polygon":
            # Save catchment area geometry data (shapes)
            shapes_data = (
                shapes["incremental"] if polygon_difference else shapes["full"]
            )
            shapes_sorted = []
            for i in shapes_data.index:
                shapes_sorted.append((shapes_data["geometry"][i], shapes_data["minute"][i]))
            shapes_sorted = sorted(shapes_sorted, key=lambda x: x[1], reverse=True)
            insert_string = ""
            for shape in shapes_sorted:
                insert_string += f"('{layer_id}', ST_MakeValid(ST_SetSRID(ST_GeomFromText('{shape[0]}'), 4326)), {shape[1]}),"
            await self.async_session.execute(
                text(f"""
                INSERT INTO {result_table} (layer_id, geom, integer_attr1)
                VALUES {insert_string.rstrip(",")};
            """)
            )
        else:
            # Save catchment area grid data
            pass

    @job_log(job_step_name="catchment_area")
    async def catchment_area(
        self,
        params: ICatchmentAreaPT,
    ) -> Dict[str, Any]:
        """Compute public transport catchment area using R5 routing endpoint."""

        if not self.job_id:
            raise ValueError("Job ID not defined")

        # Fetch starting points from previously created layer if required
        starting_pojnts = await self.get_lats_lons(
            layer_name=DefaultResultLayerName.catchment_area_starting_points,
            params=params,
        )
        lats = starting_pojnts["lats"]
        lons = starting_pojnts["lons"]
        layer_starting_points = starting_pojnts["layer_starting_points"]

        # Create feature layer to store computed catchment area output
        layer_catchment_area = IFeatureLayerToolCreate(
            name=DefaultResultLayerName.catchment_area_pt.value,
            feature_layer_geometry_type=FeatureGeometryType[
                CatchmentAreaGeometryTypeMapping[params.catchment_area_type.value]
            ],
            attribute_mapping={"integer_attr1": "travel_cost"},
            tool_type=params.tool_type.value,
            job_id=self.job_id,
        )
        result_table = f"{settings.USER_DATA_SCHEMA}.{layer_catchment_area.feature_layer_geometry_type.value}_{str(self.user_id).replace('-', '')}"

        # Compute catchment area for each starting point
        for i in range(0, len(lats)):
            # Identify relevant R5 region & bundle for this catchment area starting point
            sql_get_region_mapping = text(f"""
                SELECT r5_region_id, r5_bundle_id, r5_host
                FROM {settings.REGION_MAPPING_PT_TABLE}
                WHERE ST_INTERSECTS(
                    ST_SETSRID(
                        ST_MAKEPOINT(
                            {lons[i]},
                            {lats[i]}
                        ),
                        4326
                    ),
                    ST_SetSRID(geom, 4326)
                );
            """)
            r5_region_id, r5_bundle_id, r5_host = (
                await self.async_session.execute(sql_get_region_mapping)
            ).fetchall()[0]

            # Get relevant region bounds for this starting point
            # TODO Compute buffer distance dynamically?
            sql_get_region_bounds = text(f"""
                SELECT ST_XMin(b.geom), ST_YMin(b.geom), ST_XMax(b.geom), ST_YMax(b.geom)
                FROM (
                    SELECT ST_Envelope(
                        ST_Buffer(
                            ST_SetSRID(
                                ST_MakePoint(
                                    {lons[i]},
                                    {lats[i]}),
                                4326
                            )::geography,
                            100000
                        )::geometry
                    ) AS geom
                ) b;
            """)
            xmin, ymin, xmax, ymax = (
                await self.async_session.execute(sql_get_region_bounds)
            ).fetchall()[0]

            # Construct request payload
            request_payload = {
                "accessModes": params.routing_type.access_mode.value.upper(),
                "transitModes": ",".join(params.routing_type.mode).upper(),
                "bikeSpeed": params.bike_speed,
                "walkSpeed": params.walk_speed,
                "bikeTrafficStress": params.bike_traffic_stress,
                "date": params.time_window.weekday_date,
                "fromTime": params.time_window.from_time,
                "toTime": params.time_window.to_time,
                "maxTripDurationMinutes": params.travel_cost.max_traveltime,
                "decayFunction": {
                    "type": "logistic",
                    "standard_deviation_minutes": params.decay_function.standard_deviation_minutes,
                    "width_minutes": params.decay_function.width_minutes,
                },
                "destinationPointSetIds": [],
                "bounds": {
                    "north": ymax,
                    "south": ymin,
                    "east": xmax,
                    "west": xmin,
                },
                "directModes": params.routing_type.access_mode.value.upper(),
                "egressModes": params.routing_type.egress_mode.value.upper(),
                "fromLat": lats[i],
                "fromLon": lons[i],
                "zoom": params.zoom,
                "maxBikeTime": params.max_bike_time,
                "maxRides": params.max_rides,
                "maxWalkTime": params.max_walk_time,
                "monteCarloDraws": params.monte_carlo_draws,
                "percentiles": params.percentiles,
                "variantIndex": settings.R5_VARIANT_INDEX,
                "workerVersion": settings.R5_WORKER_VERSION,
                "regionId": r5_region_id,
                "projectId": r5_region_id,
                "bundleId": r5_bundle_id,
            }

            result = None
            try:
                # Call R5 endpoint multiple times for upto 20 seconds / 10 retries
                for i in range(settings.CRUD_NUM_RETRIES):
                    # Call R5 endpoint to compute catchment area
                    response = await self.http_client.post(
                        url=f"{r5_host}/api/analysis",
                        json=request_payload,
                        headers={"Authorization": settings.R5_AUTHORIZATION},
                    )
                    if response.status_code == 202:
                        # Engine is still processing request, retry shortly
                        if i == settings.CRUD_NUM_RETRIES - 1:
                            raise Exception(
                                "R5 engine took too long to process request."
                            )
                        await asyncio.sleep(settings.CRUD_RETRY_INTERVAL)
                        continue
                    elif response.status_code == 200:
                        # Engine has finished processing request, break
                        result = response.content
                        break
                    else:
                        raise Exception(response.text)
            except Exception as e:
                raise R5EndpointError(f"Error while calling the R5 endpoint: {str(e)}")

            catchment_area_grid = None
            catchment_area_shapes = None
            try:
                # Decode R5 response data
                catchment_area_grid = decode_r5_grid(result)

                # Convert grid data returned by R5 to valid catchment area geometry
                catchment_area_shapes = generate_jsolines(
                    grid=catchment_area_grid,
                    travel_time=params.travel_cost.max_traveltime,
                    percentile=5,
                    steps=params.travel_cost.steps,
                )
            except Exception as e:
                raise R5CatchmentAreaComputeError(
                    f"Error while processing R5 catchment area grid: {str(e)}"
                )

            try:
                # Save result to database
                await self.write_catchment_area_result(
                    catchment_area_type=params.catchment_area_type,
                    layer_id=layer_catchment_area.id,
                    result_table=result_table,
                    shapes=catchment_area_shapes,
                    grid=catchment_area_grid,
                    polygon_difference=params.polygon_difference,
                )
            except Exception as e:
                raise SQLError(
                    f"Error while saving R5 catchment area result to database: {str(e)}"
                )

            # Create new layers.
            await self.create_feature_layer_tool(
                layer_in=layer_catchment_area,
                params=params,
            )
            # Create new layer if starting points are not a layer
            if not params.starting_points.layer_project_id:
                await self.create_feature_layer_tool(
                    layer_in=layer_starting_points,
                    params=params,
                )

        return {
            "status": JobStatusType.finished.value,
            "msg": "Public transport catchment area was successfully computed.",
        }

    @run_background_or_immediately(settings)
    @job_init()
    async def run_catchment_area(self, params: ICatchmentAreaPT) -> Dict[str, Any]:
        return await self.catchment_area(params=params)


class CRUDCatchmentAreaCar(CRUDCatchmentAreaBase):
    def __init__(
        self,
        job_id: UUID,
        background_tasks: BackgroundTasks,
        async_session: AsyncSession,
        user_id: UUID,
        project_id: UUID,
        http_client: AsyncClient,
    ) -> None:
        super().__init__(job_id, background_tasks, async_session, user_id, project_id)

        self.http_client = http_client

    async def catchment_area(
        self,
        params: ICatchmentAreaCar,
        result_params: Dict[str, Any] | None = None,
    ) -> Dict[str, Any]:
        """Compute car catchment area using GOAT Routing endpoint."""

        if not self.job_id:
            raise ValueError("Job ID not defined")

        # Fetch starting points
        starting_points = await self.get_lats_lons(
            layer_name=(
                DefaultResultLayerName.catchment_area_starting_points
                if not result_params
                else result_params["starting_points_layer_name"]
            ),
            params=params,
        )
        lats = starting_points["lats"]
        lons = starting_points["lons"]
        layer_starting_points = starting_points["layer_starting_points"]

        if not result_params:
            # Create feature layer to store computed catchment area output
            layer_catchment_area = IFeatureLayerToolCreate(
                name=DefaultResultLayerName.catchment_area_active_mobility.value,
                feature_layer_geometry_type=FeatureGeometryType[
                    CatchmentAreaGeometryTypeMapping[params.catchment_area_type.value]
                ],
                attribute_mapping={"integer_attr1": "travel_cost"},
                tool_type=params.tool_type.value,
                job_id=self.job_id,
            )
            result_table = f"{settings.USER_DATA_SCHEMA}.{layer_catchment_area.feature_layer_geometry_type.value}_{str(self.user_id).replace('-', '')}"
            layer_id = layer_catchment_area.id
        else:
            layer_id = result_params["layer_id"]

        # Construct request payload
        request_payload = {
            "starting_points": {
                "latitude": lats,
                "longitude": lons,
            },
            "routing_type": params.routing_type.value,
            "travel_cost": (
                {
                    "max_traveltime": params.travel_cost.max_traveltime,
                    "steps": params.travel_cost.steps,
                }
                if type(params.travel_cost)
                is CatchmentAreaTravelTimeCostMotorizedMobility
                else {
                    "max_distance": params.travel_cost.max_distance,
                    "steps": params.travel_cost.steps,
                }
            ),
            "catchment_area_type": params.catchment_area_type.value,
            "polygon_difference": params.polygon_difference,
            "result_table": (
                result_table if not result_params else result_params["result_table"]
            ),
            "layer_id": str(layer_id),
        }

        # Append scenario ID if specified
        if params.scenario_id:
            request_payload["scenario_id"] = str(params.scenario_id)

        # Append street network config if specified
        if params.street_network:
            request_payload["street_network"] = {
                "edge_layer_project_id": params.street_network.edge_layer_project_id,
                "node_layer_project_id": params.street_network.node_layer_project_id,
            }

        await call_routing_endpoint(
            params.routing_type, request_payload, self.http_client
        )

        # Create layers only if result_params are not provided
        if not result_params:
            # Create new layers.
            await self.create_feature_layer_tool(
                layer_in=layer_catchment_area,
                params=params,
            )

        # Create new layer if starting points are not a layer
        if not params.starting_points.layer_project_id:
            await self.create_feature_layer_tool(
                layer_in=layer_starting_points,
                params=params,
            )

        return {
            "status": JobStatusType.finished.value,
            "msg": "Active mobility catchment area was successfully computed.",
        }

    @job_log(job_step_name="catchment_area")
    async def catchment_area_job(self, params: ICatchmentAreaCar) -> Dict[str, Any]:
        return await self.catchment_area(params=params)

    @run_background_or_immediately(settings)
    @job_init()
    async def run_catchment_area(self, params: ICatchmentAreaCar) -> Dict[str, Any]:
        return await self.catchment_area_job(params=params)
