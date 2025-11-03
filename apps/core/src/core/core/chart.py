from typing import Any, List
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from core.crud.crud_layer_project import layer_project as crud_layer_project
from core.db.models.layer import Layer, ToolType
from core.schemas.project import (
    IFeatureStandardProjectRead,
    IFeatureToolProjectRead,
)
from core.schemas.toolbox_base import ColumnStatisticsOperation
from core.utils import search_value


async def read_chart_data(
    async_session: AsyncSession,
    project_id: UUID,
    layer_project_id: int,
    cumsum: bool = False,
) -> dict[str, Any]:
    # Get layer project data
    layer_project = await crud_layer_project.get_internal(
        async_session=async_session, project_id=project_id, id=layer_project_id
    )

    # Make sure that layer is aggregation_point or aggregation_polygon
    if layer_project.tool_type not in [
        ToolType.aggregate_point,
        ToolType.aggregate_polygon,
    ]:
        raise ValueError("Layer is not aggregation point or aggregation polygon")

    # Get chart data
    charts = layer_project.charts
    operation = charts["operation"]
    x_label = charts["x_label"]
    y_label = charts["y_label"]
    group_by = charts.get("group_by")

    if cumsum:
        operation = ColumnStatisticsOperation.sum

    # Get y_query
    x_label_mapped = search_value(layer_project.attribute_mapping, x_label)
    y_label_mapped = search_value(layer_project.attribute_mapping, y_label)

    # Replace count with sum in case operation is count
    if operation == ColumnStatisticsOperation.count:
        operation = ColumnStatisticsOperation.sum

    if not group_by:
        # Define statistics query
        y_query = crud_layer_project.get_statistics_sql(y_label_mapped, operation)
        # Get data from layer

        sql_base = f"""
            SELECT {x_label_mapped} AS x, {y_query} AS y
            FROM {layer_project.table_name}
            WHERE layer_id = '{layer_project.layer_id}'
            GROUP BY {x_label_mapped}
            ORDER BY {x_label_mapped}
        """
        if cumsum is False:
            sql = f"""
                WITH data AS (
                    {sql_base}
                )
                SELECT jsonb_agg(x), jsonb_agg(y)
                FROM data
            """
        else:
            sql = f"""
                WITH data AS (
                    {sql_base}
                ),
                cumsum AS (
                    SELECT x, SUM(y) OVER (ORDER BY x) AS y
                    FROM data
                )
                SELECT jsonb_agg(x), jsonb_agg(y)
                FROM cumsum
            """
    else:
        # Define statistics query
        y_query = crud_layer_project.get_statistics_sql("value", operation)

        # Cast value inside query to float
        y_query = y_query.replace("value", "value::float")
        # Use the original operation here since operation might have been changed
        data_column = search_value(
            layer_project.attribute_mapping, charts["operation"] + "_grouped"
        )

        # Build query
        sql_base = f"""
            SELECT {x_label_mapped} x, key AS group, {y_query} AS y
            FROM {layer_project.table_name}, LATERAL JSONB_EACH({data_column})
            WHERE layer_id = '{layer_project.layer_id}'
            GROUP BY {x_label_mapped}, key
            ORDER BY {x_label_mapped}, key
        """
        # Adjust query based on cumsum
        if cumsum is False:
            sql = f"""
                WITH unnested AS (
                    {sql_base}
                ),
                grouped AS
                (
                    SELECT jsonb_agg(x) AS x, jsonb_agg(y) as y, "group"
                    FROM unnested
                    GROUP BY "group"
                )
                SELECT jsonb_agg(x) x, jsonb_agg(y), jsonb_agg("group")
                FROM grouped
            """
        else:
            sql = f"""
                WITH unnested AS (
                    {sql_base}
                ),
                grouped AS (
                    SELECT x, "group",
                    SUM(y) OVER (PARTITION BY "group" ORDER BY x) AS y -- Calculate cumulative sum of y within each group
                    FROM unnested
                ),
                second_grouped AS
                (
                    SELECT jsonb_agg(x) AS x, jsonb_agg(y) AS y, "group"
                    FROM grouped
                    GROUP BY "group"
                )
                SELECT jsonb_agg(x) AS x, jsonb_agg(y) AS y, jsonb_agg("group")
                FROM second_grouped
            """

    result = (await async_session.execute(text(sql))).fetchall()
    data = {
        "x": result[0][0],
        "y": result[0][1],
        "group": result[0][2] if group_by else None,
    }
    return data


class Chart:
    def __init__(
        self,
        job_id: UUID | None,
        async_session: AsyncSession,
        user_id: UUID,
    ) -> None:
        self.job_id = job_id
        self.async_session = async_session
        self.user_id = user_id

    async def create_chart(
        self,
        layer: Layer,
        layer_project: IFeatureStandardProjectRead | IFeatureToolProjectRead,
        operation: ColumnStatisticsOperation,
        x_label: str,
        y_label: str,
        group_by: List[str] | None = None,
    ) -> None:
        # Map columns
        chart_data = {
            "charts": {
                "operation": operation.value,
                "x_label": x_label,
                "y_label": y_label,
                "group_by": group_by,
            }
        }

        # Update layer project with chart data
        await crud_layer_project.update(
            async_session=self.async_session, id=layer_project.id, layer_in=chart_data
        )
