from typing import Any, Dict
from uuid import UUID

from fastapi import BackgroundTasks
from sqlalchemy import TextClause, text
from sqlalchemy.ext.asyncio import AsyncSession

from core.core.config import settings
from core.core.job import job_init, job_log, run_background_or_immediately
from core.core.tool import CRUDToolBase
from core.db.models.layer import FeatureGeometryType
from core.schemas.heatmap import (
    TRAVELTIME_MATRIX_RESOLUTION,
    TRAVELTIME_MATRIX_TABLE,
    ActiveRoutingHeatmapType,
    IHeatmapConnectivityActive,
    IHeatmapConnectivityMotorized,
    MotorizedRoutingHeatmapType,
)
from core.schemas.job import JobStatusType
from core.schemas.layer import IFeatureLayerToolCreate
from core.schemas.project import (
    IFeatureStandardProjectRead,
    IFeatureToolProjectRead,
)
from core.schemas.toolbox_base import DefaultResultLayerName
from core.utils import format_value_null_sql


class CRUDHeatmapConnectivity(CRUDToolBase):
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
        layer_project: IFeatureStandardProjectRead | IFeatureToolProjectRead,
        scenario_id: UUID | None,
    ) -> str:
        """Create distributed table for user-specified opportunities."""

        # Create temp table name for points
        temp_points = await self.create_temp_table_name("points")

        # Create distributed point table using sql
        await self.async_session.execute(
            text(f"""SELECT basic.create_heatmap_connectivity_reference_area_table(
                {layer_project.id},
                '{layer_project.table_name}',
                '{settings.CUSTOMER_SCHEMA}',
                {format_value_null_sql(scenario_id)},
                '{layer_project.where_query.replace("'", "''")}',
                '{temp_points}',
                {TRAVELTIME_MATRIX_RESOLUTION[routing_type]},
                {False}
            )""")
        )
        await self.async_session.commit()

        return temp_points

    def build_query(
        self,
        params: IHeatmapConnectivityActive | IHeatmapConnectivityMotorized,
        reference_area_table: str,
        result_table: str,
        result_layer_id: str,
    ) -> TextClause:
        """Builds SQL query to compute heatmap connectivity."""

        h3_cell_area = f"((3 * SQRT(3) / 2) * POWER(h3_get_hexagon_edge_length_avg({TRAVELTIME_MATRIX_RESOLUTION[params.routing_type]}, 'm'), 2))"

        query = text(f"""
            INSERT INTO {result_table} (layer_id, geom, text_attr1, float_attr1)
            SELECT '{result_layer_id}', ST_SetSRID(h3_cell_to_boundary(matrix.orig_id)::geometry, 4326),
                matrix.orig_id, SUM(ARRAY_LENGTH(matrix.dest_id, 1) * {h3_cell_area})
            FROM {reference_area_table} o, {TRAVELTIME_MATRIX_TABLE[params.routing_type]} matrix
            WHERE matrix.h3_3 = o.h3_3
            AND matrix.orig_id = o.h3_index
            AND matrix.traveltime <= {params.max_traveltime}
            GROUP BY matrix.orig_id;
        """)
        return query

    @job_log(job_step_name="heatmap_connectivity")
    async def heatmap(
        self,
        params: IHeatmapConnectivityActive | IHeatmapConnectivityMotorized,
    ) -> Dict[str, Any]:
        """Compute heatmap connectivity."""

        if not self.job_id:
            raise ValueError("Job ID not defined")

        # Fetch reference area table
        reference_area_layer = await self.get_layers_project(params)
        reference_area_table = await self.create_distributed_opportunity_table(
            params.routing_type,
            reference_area_layer["reference_area_layer_project_id"],
            params.scenario_id,
        )

        # Initialize result table
        result_table = f"{settings.USER_DATA_SCHEMA}.{FeatureGeometryType.polygon.value}_{str(self.user_id).replace('-', '')}"

        # Create feature layer to store computed heatmap output
        layer_heatmap = IFeatureLayerToolCreate(
            name=(
                DefaultResultLayerName.heatmap_connectivity_active_mobility.value
                if type(params.routing_type) is ActiveRoutingHeatmapType
                else DefaultResultLayerName.heatmap_connectivity_motorized_mobility.value
            ),
            feature_layer_geometry_type=FeatureGeometryType.polygon,
            attribute_mapping={
                "text_attr1": "h3_index",
                "float_attr1": "accessibility",
            },
            tool_type=params.tool_type.value,
            job_id=self.job_id,
        )

        # Compute heatmap & write to output table
        await self.async_session.execute(
            self.build_query(
                params=params,
                reference_area_table=reference_area_table,
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
            "msg": "Heatmap connectivity was successfully computed.",
        }

    @run_background_or_immediately(settings)
    @job_init()
    async def run_heatmap(
        self,
        params: IHeatmapConnectivityActive | IHeatmapConnectivityMotorized,
    ) -> Dict[str, Any]:
        return await self.heatmap(params=params)
