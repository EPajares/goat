from typing import Any, Dict, List, Tuple
from uuid import UUID

from fastapi import BackgroundTasks
from sqlalchemy import TextClause, text
from sqlalchemy.ext.asyncio import AsyncSession

from core.core.config import settings
from core.core.job import job_init, job_log, run_background_or_immediately
from core.crud.crud_heatmap import CRUDHeatmapBase
from core.db.models.layer import FeatureGeometryType
from core.schemas.heatmap import (
    ROUTING_MODE_DEFAULT_SPEED,
    TRAVELTIME_MATRIX_RESOLUTION,
    TRAVELTIME_MATRIX_TABLE,
    ActiveRoutingHeatmapType,
    IHeatmapGravityActive,
    IHeatmapGravityMotorized,
    ImpedanceFunctionType,
    MotorizedRoutingHeatmapType,
)
from core.schemas.job import JobStatusType
from core.schemas.layer import IFeatureLayerToolCreate
from core.schemas.project import IFeatureStandardProjectRead, IFeatureToolProjectRead
from core.schemas.toolbox_base import DefaultResultLayerName
from core.utils import (
    format_value_null_sql,
    search_value,
)


class CRUDHeatmapGravity(CRUDHeatmapBase):
    def __init__(
        self,
        job_id: UUID,
        background_tasks: BackgroundTasks,
        async_session: AsyncSession,
        user_id: UUID,
        project_id: UUID,
    ) -> None:
        super().__init__(job_id, background_tasks, async_session, user_id, project_id)

    async def create_distributed_opportunity_table(
        self,
        routing_type: ActiveRoutingHeatmapType | MotorizedRoutingHeatmapType,
        layers: List[Dict[str, Any]],
        scenario_id: UUID | None,
        opportunity_geofence_layer: IFeatureStandardProjectRead
        | IFeatureToolProjectRead
        | None,
    ) -> Tuple[str, str | None]:
        """Create distributed table for user-specified opportunities."""

        # Create temp table name for points
        temp_points = await self.create_temp_table_name("points")

        # Create temp table name for filler cells
        temp_filler_cells = None
        for layer in layers:
            if layer["geom_type"] == FeatureGeometryType.polygon:
                # Create temp table name for filler cells
                temp_filler_cells = await self.create_temp_table_name("filler_cells")
                break

        # Create formatted opportunity geofence layer strings for SQL query
        geofence_table = (
            "NULL"
            if opportunity_geofence_layer is None
            else f"'{opportunity_geofence_layer.table_name}'"
        )
        geofence_where_filter = "NULL"
        if opportunity_geofence_layer is not None:
            geofence_where_filter = opportunity_geofence_layer.where_query.replace(
                "'", "''"
            )
            geofence_where_filter = f"'{geofence_where_filter}'"

        append_to_existing = False
        for layer in layers:
            # Compute geofence buffer distance
            geofence_buffer_dist = (
                layer["layer"].max_traveltime
                * ((ROUTING_MODE_DEFAULT_SPEED[routing_type] * 1000) / 60)
                if opportunity_geofence_layer is not None
                else "NULL"
            )

            # Prepare destination potential column
            destination_potential_column = layer["layer"].destination_potential_column
            if destination_potential_column == "$area":
                # The computed area of polygons in the opportunity layer will be used
                destination_potential_column = "'ST_Area(geom::geography)'"
            elif not destination_potential_column:
                # A destination potential column was not specified
                destination_potential_column = "1::text"
            else:
                # Fetch the specified destination potential column from the attribute mapping
                destination_potential_column = search_value(
                    layer["layer_project"].attribute_mapping,
                    destination_potential_column,
                )
                destination_potential_column = f"'{destination_potential_column}'"

            # Create temporary distributed table from supplied opportunity layer
            await self.async_session.execute(
                text(f"""SELECT basic.create_heatmap_gravity_opportunity_table(
                    {layer["layer"].opportunity_layer_project_id},
                    '{layer["table_name"]}',
                    '{settings.CUSTOMER_SCHEMA}',
                    {format_value_null_sql(scenario_id)},
                    {geofence_table},
                    {geofence_where_filter},
                    {geofence_buffer_dist},
                    {layer["layer"].max_traveltime},
                    {layer["layer"].sensitivity},
                    {destination_potential_column},
                    '{layer["where_query"].replace("'", "''")}',
                    '{temp_points}',
                    {TRAVELTIME_MATRIX_RESOLUTION[routing_type]},
                    {layer["geom_type"] == FeatureGeometryType.polygon},
                    {format_value_null_sql(temp_filler_cells)},
                    {append_to_existing}
                )""")
            )

            await self.async_session.commit()
            append_to_existing = True

        return temp_points, temp_filler_cells

    def build_impedance_function(
        self,
        type: ImpedanceFunctionType,
        max_traveltime: int,
        max_sensitivity: float,
    ) -> str:
        """Builds impedance function used to compute heatmap gravity."""

        if type == ImpedanceFunctionType.gaussian:
            return f"SUM((EXP(1) ^ ((((traveltime / {float(max_traveltime)}) ^ 2) * -1) / (sensitivity / {max_sensitivity}))) * potential)"
        elif type == ImpedanceFunctionType.linear:
            return f"SUM((1 - (traveltime / {float(max_traveltime)})) * potential)"
        elif type == ImpedanceFunctionType.exponential:
            return f"SUM((EXP(1) ^ (((sensitivity / {max_sensitivity}) * -1) * (traveltime / {float(max_traveltime)}))) * potential)"
        elif type == ImpedanceFunctionType.power:
            return f"SUM(((traveltime / {float(max_traveltime)}) ^ ((sensitivity / {max_sensitivity}) * -1)) * potential)"
        else:
            raise ValueError(f"Unknown impedance function type: {type}")

    def build_query(
        self,
        params: IHeatmapGravityActive | IHeatmapGravityMotorized,
        opportunity_table: str,
        filler_cells_table: str | None,
        max_traveltime: int,
        max_sensitivity: float,
        result_table: str,
        result_layer_id: str,
    ) -> TextClause:
        """Builds SQL query to compute heatmap gravity."""

        impedance_function = self.build_impedance_function(
            type=params.impedance_function,
            max_traveltime=max_traveltime,
            max_sensitivity=max_sensitivity,
        )

        query = f"""
            SELECT dest_id, {impedance_function} AS accessibility
            FROM (
                SELECT opportunity_id, dest_id.value AS dest_id, min(traveltime) AS traveltime, sensitivity, potential
                FROM
                (
                    SELECT opportunity.id AS opportunity_id, matrix.orig_id, matrix.dest_id, CAST(matrix.traveltime AS float) AS traveltime,
                        opportunity.sensitivity, opportunity.potential
                    FROM {opportunity_table} opportunity, {TRAVELTIME_MATRIX_TABLE[params.routing_type]} matrix
                    WHERE matrix.h3_3 = opportunity.h3_3
                    AND matrix.orig_id = opportunity.h3_index
                    AND matrix.traveltime <= opportunity.max_traveltime
                ) sub_matrix
                JOIN LATERAL UNNEST(sub_matrix.dest_id) dest_id(value) ON TRUE
                GROUP BY opportunity_id, dest_id.value, sensitivity, potential
            ) grouped_opportunities
            GROUP BY dest_id
        """

        if filler_cells_table:
            query += f"""
                UNION ALL
                SELECT h3_index AS dest_id, {impedance_function} AS accessibility
                FROM (
                    SELECT *, 1.0 AS traveltime
                    FROM {filler_cells_table}
                ) filler_cells
                GROUP BY h3_index
            """

        return text(f"""
            INSERT INTO {result_table} (layer_id, geom, text_attr1, float_attr1)
            SELECT
                '{result_layer_id}',
                ST_SetSRID(h3_cell_to_boundary(dest_id)::geometry, 4326),
                dest_id,
                MAX(accessibility)
            FROM (
                {query}
            ) result
            GROUP BY dest_id;
        """)

    @job_log(job_step_name="heatmap_gravity")
    async def heatmap(
        self, params: IHeatmapGravityActive | IHeatmapGravityMotorized
    ) -> Dict[str, Any]:
        """Compute heatmap gravity."""

        if not self.job_id:
            raise ValueError("Job ID not defined")

        # Fetch opportunity tables
        layers, opportunity_geofence_layer = await self.fetch_opportunity_layers(params)
        (
            opportunity_table,
            filler_cells_table,
        ) = await self.create_distributed_opportunity_table(
            params.routing_type,
            layers,
            params.scenario_id,
            opportunity_geofence_layer,
        )

        # Initialize result table
        result_table = f"{settings.USER_DATA_SCHEMA}.{FeatureGeometryType.polygon.value}_{str(self.user_id).replace('-', '')}"

        # Create feature layer to store computed heatmap output
        layer_heatmap = IFeatureLayerToolCreate(
            name=(
                DefaultResultLayerName.heatmap_gravity_active_mobility.value
                if type(params.routing_type) is ActiveRoutingHeatmapType
                else DefaultResultLayerName.heatmap_gravity_motorized_mobility.value
            ),
            feature_layer_geometry_type=FeatureGeometryType.polygon,
            attribute_mapping={
                "text_attr1": "h3_index",
                "float_attr1": "accessibility",
            },
            tool_type=params.tool_type.value,
            job_id=self.job_id,
        )

        # Get max traveltime & sensitivity for normalization
        max_traveltime = max([layer["layer"].max_traveltime for layer in layers])

        # Compute heatmap & write to result table
        await self.async_session.execute(
            self.build_query(
                params=params,
                opportunity_table=opportunity_table,
                filler_cells_table=filler_cells_table,
                max_traveltime=max_traveltime,
                max_sensitivity=settings.HEATMAP_GRAVITY_MAX_SENSITIVITY,
                result_table=result_table,
                result_layer_id=str(layer_heatmap.id),
            )
        )

        # Register feature layer
        await self.create_feature_layer_tool(
            layer_in=layer_heatmap,
            params=params,
        )

        return {
            "status": JobStatusType.finished.value,
            "msg": "Heatmap gravity was successfully computed.",
        }

    @run_background_or_immediately(settings)
    @job_init()
    async def run_heatmap(
        self, params: IHeatmapGravityActive | IHeatmapGravityMotorized
    ) -> Dict[str, Any]:
        return await self.heatmap(params=params)
