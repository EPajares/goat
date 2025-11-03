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
from core.db.models.layer import FeatureGeometryType, ToolType
from core.schemas.job import JobStatusType
from core.schemas.layer import IFeatureLayerToolCreate, UserDataGeomType
from core.schemas.toolbox_base import DefaultResultLayerName
from core.schemas.trip_count_station import (
    ITripCountStation,
    public_transport_types,
)
from core.utils import build_where_clause, format_value_null_sql


class CRUDTripCountStation(CRUDToolBase):
    """CRUD for PT Trip Count."""

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

    @job_log(job_step_name="trip_count_station")
    async def trip_count(self, params: ITripCountStation) -> Dict[str, Any]:
        if not self.job_id:
            raise ValueError("Job ID not defined")

        # Get Layer
        layer_project = (await self.get_layers_project(params=params))[
            "reference_area_layer_project_id"
        ]

        input_table = layer_project.table_name
        where_query = build_where_clause([layer_project.where_query])

        # Create result layer object
        pt_modes = list(public_transport_types.keys())
        pt_modes.append("total")

        # Populate attribute mapping with pt_modes as integer
        attribute_mapping = {
            f"integer_attr{i+1}": pt_mode for i, pt_mode in enumerate(pt_modes)
        }
        attribute_mapping = {
            "text_attr1": "stop_id",
            "text_attr2": "stop_name",
            "jsonb_attr1": "trip_cnt",
        } | attribute_mapping

        result_layer = IFeatureLayerToolCreate(
            name=DefaultResultLayerName.trip_count_station.value,
            feature_layer_geometry_type=FeatureGeometryType[
                UserDataGeomType.point.value
            ],
            attribute_mapping=attribute_mapping,
            tool_type=ToolType.trip_count_station,
            job_id=self.job_id,
        )

        # Create mapping for transport modes
        flat_mode_mapping = {}
        for outer_key, inner_dict in public_transport_types.items():
            for inner_key in inner_dict:
                flat_mode_mapping[str(inner_key)] = outer_key

        # Get trip count using sql function
        sql_query = text(f"""
            INSERT INTO {self.result_table}(layer_id, geom, {', '.join(result_layer.attribute_mapping.keys())})
            SELECT '{str(result_layer.id)}', s.geom, s.stop_id, s.stop_name, s.trip_cnt,
            (summarized ->> 'bus')::integer AS bus, (summarized ->> 'tram')::integer AS tram, (summarized ->> 'metro')::integer AS metro,
            (summarized ->> 'rail')::integer AS rail, (summarized ->> 'other')::integer AS other,
            (summarized ->> 'bus')::integer + (summarized ->> 'tram')::integer + (summarized ->> 'metro')::integer +
            (summarized ->> 'rail')::integer + (summarized ->> 'other')::integer AS total
            FROM basic.count_public_transport_services_station(
                '{input_table}',
                {layer_project.id},
                '{settings.CUSTOMER_SCHEMA}',
                {format_value_null_sql(params.scenario_id)},
                :where_query,
                '{str(timedelta(seconds=params.time_window.from_time))}',
                '{str(timedelta(seconds=params.time_window.to_time))}',
                {params.time_window.weekday_integer}
            ) s, LATERAL basic.summarize_trip_count(trip_cnt, '{json.dumps(flat_mode_mapping)}'::JSONB) summarized
        """)
        await self.async_session.execute(sql_query, {"where_query": where_query})
        await self.async_session.commit()

        # Create result layer
        await self.create_feature_layer_tool(layer_in=result_layer, params=params)
        return {
            "status": JobStatusType.finished.value,
            "msg": "Trip count created.",
        }

    @run_background_or_immediately(settings)
    @job_init()
    async def trip_count_run(self, params: ITripCountStation) -> Dict[str, Any]:
        return await self.trip_count(params=params)
