from typing import Any, Dict
from uuid import UUID

from fastapi import BackgroundTasks
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from core.core.config import settings
from core.core.job import job_init, job_log, run_background_or_immediately
from core.core.layer import get_user_table
from core.core.tool import CRUDToolBase
from core.db.models.layer import ToolType
from core.schemas.job import JobStatusType, JobType
from core.schemas.layer import (
    IFeatureLayerToolCreate,
)
from core.schemas.tool import IJoin
from core.schemas.toolbox_base import DefaultResultLayerName
from core.utils import (
    build_where_clause,
    get_result_column,
    search_value,
)


class CRUDJoin(CRUDToolBase):
    def __init__(
        self,
        job_id: UUID,
        background_tasks: BackgroundTasks,
        async_session: AsyncSession,
        user_id: UUID,
        project_id: UUID,
    ) -> None:
        super().__init__(job_id, background_tasks, async_session, user_id, project_id)

    @job_log(JobType.join.value)
    async def join(
        self,
        params: IJoin,
    ) -> Dict[str, Any]:
        if not self.job_id:
            raise ValueError("Job ID not defined")

        # Get layers
        layers_project = await self.get_layers_project(
            params=params,
        )
        target_layer_project = layers_project["target_layer_project_id"]
        join_layer_project = layers_project["join_layer_project_id"]

        # Get translated fields
        mapped_target_field = search_value(
            target_layer_project.attribute_mapping, params.target_field
        )
        mapped_join_field = search_value(
            join_layer_project.attribute_mapping, params.join_field
        )

        # Check if mapped statistics field is float, integer or biginteger
        mapped_statistics_field = await self.check_column_statistics(
            layer_project=join_layer_project,
            column_name=params.column_statistics.field,
            operation=params.column_statistics.operation,
        )
        mapped_statistics_field = mapped_statistics_field["mapped_statistics_field"]

        # Get result column name
        result_column = get_result_column(
            attribute_mapping=target_layer_project.attribute_mapping,
            base_column_name=params.column_statistics.operation.value,
            datatype=mapped_statistics_field.split("_")[0],
        )
        new_layer_attribute_mapping = target_layer_project.attribute_mapping.copy()
        new_layer_attribute_mapping.update(result_column)

        # Create new layer
        layer_in = IFeatureLayerToolCreate(
            name=DefaultResultLayerName.join.value,
            feature_layer_geometry_type=target_layer_project.feature_layer_geometry_type,
            attribute_mapping=new_layer_attribute_mapping,
            tool_type=ToolType.join.value,
            job_id=self.job_id,
        )

        # Update user_id in target_layer_projet to meet the user_id of the user sending the request
        copy_target_layer_project = target_layer_project.copy(
            update={"user_id": self.user_id}
        )
        result_table = get_user_table(copy_target_layer_project)

        # Create insert statement
        insert_columns = (
            ", ".join(target_layer_project.attribute_mapping.keys())
            + ", "
            + list(result_column.keys())[0]
        )
        select_columns = ", ".join(
            "target_layer." + value
            for value in ["geom"] + list(target_layer_project.attribute_mapping.keys())
        )
        insert_statement = (
            f"INSERT INTO {result_table} (layer_id, geom, {insert_columns})"
        )

        # Get statistics column query
        statistics_column_query = self.get_statistics_sql(
            "join_layer." + mapped_statistics_field,
            operation=params.column_statistics.operation,
        )

        # Build combined where query
        where_query = build_where_clause(
            [
                target_layer_project.where_query.replace(
                    f"{target_layer_project.table_name}.", "target_layer."
                ),
                join_layer_project.where_query.replace(
                    f"{join_layer_project.table_name}.", "join_layer."
                ),
            ],
        )

        # Create query
        sql_query = (
            insert_statement
            + f"""
            SELECT '{layer_in.id}', {select_columns}, {statistics_column_query}
            FROM {target_layer_project.table_name} target_layer
            LEFT JOIN {join_layer_project.table_name} join_layer
            ON target_layer.{mapped_target_field}::text = join_layer.{mapped_join_field}::text
            {where_query}
            GROUP BY {select_columns}
        """
        )

        # Execute query
        await self.async_session.execute(text(sql_query))

        # Create new layer
        await self.create_feature_layer_tool(
            layer_in=layer_in,
            params=params,
        )
        return {
            "status": JobStatusType.finished.value,
            "msg": "Layers where successfully joined.",
        }

    @run_background_or_immediately(settings)
    @job_init()
    async def join_run(self, params: IJoin) -> Dict[str, Any]:
        return await self.join(params=params)
