from typing import Any, Dict
from uuid import UUID

from fastapi import BackgroundTasks
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from core.core.config import settings
from core.core.job import job_init, job_log, run_background_or_immediately
from core.core.tool import CRUDToolBase
from core.schemas.job import JobStatusType
from core.schemas.layer import FeatureGeometryType, IFeatureLayerToolCreate
from core.schemas.tool import IBuffer
from core.schemas.toolbox_base import DefaultResultLayerName


class CRUDBuffer(CRUDToolBase):
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
            f"{settings.USER_DATA_SCHEMA}.polygon_{str(self.user_id).replace('-', '')}"
        )

    @job_log(job_step_name="buffer")
    async def buffer(self, params: IBuffer) -> Dict[str, Any]:
        if not self.job_id:
            raise ValueError("Job ID not defined")

        # Get layers
        layer_project = await self.get_layers_project(
            params=params,
        )
        layer_project = layer_project["source_layer_project_id"]
        # Create layer object for results
        layer_result = IFeatureLayerToolCreate(
            name=DefaultResultLayerName[params.tool_type].value,
            feature_layer_geometry_type=FeatureGeometryType.polygon,
            attribute_mapping={"integer_attr1": "radius_size"},
            tool_type=params.tool_type,
            job_id=self.job_id,
        )
        # Create distributed table depending on feature layer geometry type
        function_mapping = {
            FeatureGeometryType.point: self.create_distributed_point_table,
            FeatureGeometryType.polygon: self.create_distributed_polygon_table,
            FeatureGeometryType.line: self.create_distributed_line_table,
        }
        temp_table_name = await function_mapping[
            layer_project.feature_layer_geometry_type
        ](layer_project=layer_project, scenario_id=params.scenario_id)

        # Buffer steps based on params.max_distance and params.distance_step
        steps = []
        step_size = params.max_distance / params.distance_step
        for i in range(params.distance_step):
            steps.append(step_size + (i * step_size))
        if params.polygon_union:
            # Build buffer query
            sql_buffer_query = f"""
			SELECT '{layer_result.id}', ST_UNION(geom) geom, buffer_size
			FROM
			(
				SELECT ST_UNION(ST_BUFFER(geom::geography, buffer_size)::geometry) geom, buffer_size
				FROM {temp_table_name}, UNNEST(ARRAY{steps}) buffer_size
				GROUP BY h3_3, buffer_size
			) x
			GROUP BY buffer_size
            ORDER BY buffer_size
			"""
        else:
            # Build buffer query
            sql_buffer_query = f"""
            SELECT '{layer_result.id}', ST_UNION(ST_BUFFER(geom::geography, buffer_size)::geometry) geom, buffer_size
            FROM {temp_table_name}, UNNEST(ARRAY{steps}) buffer_size
            GROUP BY id, buffer_size
            ORDER BY buffer_size
            """

        # Create wrapper for polygon difference between buffer steps using CROSS JOIN LATERAL
        if params.polygon_difference:
            # Build buffer query
            sql_combined_query = text(f"""
            INSERT INTO {self.result_table}(layer_id, geom, integer_attr1)
            WITH buffered AS
            (
                {sql_buffer_query}
            ),
            diff AS
            (
                SELECT '{layer_result.id}'::UUID, ST_DIFFERENCE(geom, geom_prev) geom, buffer_size
                FROM buffered x
                CROSS JOIN LATERAL
                (
                    SELECT geom geom_prev
                    FROM buffered y
                    WHERE y.buffer_size = x.buffer_size - {step_size}
                ) y
                WHERE x.buffer_size > {step_size}
                UNION ALL
                SELECT '{layer_result.id}'::UUID, geom, buffer_size
                FROM buffered
                WHERE buffer_size = {step_size}
            )
            SELECT *
            FROM diff
            ORDER BY buffer_size
            """)
        else:
            sql_combined_query = text(f"""
            INSERT INTO {self.result_table}(layer_id, geom, integer_attr1)
            {sql_buffer_query}
            """)
        # Execute query
        await self.async_session.execute(sql_combined_query)
        await self.async_session.commit()

        # Create new layer
        await self.create_feature_layer_tool(
            layer_in=layer_result,
            params=params,
        )

        # Delete temporary tables
        await self.delete_temp_tables()

        return {
            "status": JobStatusType.finished.value,
            "msg": "Feature were successfully buffered.",
        }

    @run_background_or_immediately(settings)
    @job_init()
    async def buffer_run(self, params: IBuffer) -> Dict[str, Any]:
        return await self.buffer(params=params)
