from typing import Any, Dict, List, Tuple
from uuid import UUID

from fastapi import BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession

from core.core.tool import CRUDToolBase
from core.crud.crud_layer_project import layer_project as crud_layer_project
from core.schemas.heatmap import (
    IHeatmapClosestAverageActive,
    IHeatmapClosestAverageMotorized,
    IHeatmapGravityActive,
    IHeatmapGravityMotorized,
)
from core.schemas.project import IFeatureStandardProjectRead, IFeatureToolProjectRead


class CRUDHeatmapBase(CRUDToolBase):
    def __init__(
        self,
        job_id: UUID,
        background_tasks: BackgroundTasks,
        async_session: AsyncSession,
        user_id: UUID,
        project_id: UUID,
    ) -> None:
        super().__init__(job_id, background_tasks, async_session, user_id, project_id)

    async def fetch_opportunity_layers(
        self,
        params: (
            IHeatmapGravityActive
            | IHeatmapGravityMotorized
            | IHeatmapClosestAverageActive
            | IHeatmapClosestAverageMotorized
        ),
    ) -> Tuple[
        List[Dict[str, Any]],
        IFeatureStandardProjectRead | IFeatureToolProjectRead | None,
    ]:
        # Iterate over opportunity layers supplied by user
        opportunity_layers = []
        for layer in params.opportunities:
            # Get project for this layer
            input_layer_types = params.input_layer_types
            layer_project = await crud_layer_project.get_internal(
                async_session=self.async_session,
                id=layer.opportunity_layer_project_id,
                project_id=self.project_id,
                expected_layer_types=input_layer_types[
                    "opportunity_layer_project_id"
                ].layer_types,
                expected_geometry_types=input_layer_types[
                    "opportunity_layer_project_id"
                ].feature_layer_geometry_types,
            )

            # Check Max feature count
            await self.check_max_feature_cnt(
                layers_project=[layer_project],
                tool_type=params.tool_type,
            )

            opportunity_layers.append(
                {
                    "table_name": layer_project.table_name,
                    "where_query": layer_project.where_query,
                    "geom_type": layer_project.feature_layer_geometry_type,
                    "layer": layer,
                    "layer_project": layer_project,
                }
            )

        # Get opportunity geofence layer if specified
        opportunity_geofence_layer = None
        if params.opportunity_geofence_layer_project_id:
            opportunity_geofence_layer = (await self.get_layers_project(params=params))[
                "opportunity_geofence_layer_project_id"
            ]

        return opportunity_layers, opportunity_geofence_layer
