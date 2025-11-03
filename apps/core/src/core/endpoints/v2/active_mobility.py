from fastapi import APIRouter, Body, Depends

from core.core.tool import start_calculation
from core.crud.crud_catchment_area import CRUDCatchmentAreaActiveMobility
from core.crud.crud_heatmap_closest_average import CRUDHeatmapClosestAverage
from core.crud.crud_heatmap_connectivity import CRUDHeatmapConnectivity
from core.crud.crud_heatmap_gravity import CRUDHeatmapGravity
from core.deps.auth import auth_z
from core.endpoints.deps import get_http_client
from core.schemas.catchment_area import (
    ICatchmentAreaActiveMobility,
)
from core.schemas.catchment_area import (
    request_examples_catchment_area_active_mobility as active_mobility_request_examples,
)
from core.schemas.heatmap import (
    IHeatmapClosestAverageActive,
    IHeatmapConnectivityActive,
    IHeatmapGravityActive,
)
from core.schemas.job import JobType
from core.schemas.toolbox_base import CommonToolParams, IToolResponse

router = APIRouter()


@router.post(
    "/catchment-area",
    summary="Compute catchment areas for active mobility",
    response_model=IToolResponse,
    status_code=201,
    dependencies=[Depends(auth_z)],
)
async def compute_active_mobility_catchment_area(
    *,
    common: CommonToolParams = Depends(),
    params: ICatchmentAreaActiveMobility = Body(
        ...,
        example=active_mobility_request_examples["catchment_area_active_mobility"],
        description="The catchment area parameters.",
    ),
) -> IToolResponse:
    """Compute catchment areas for active mobility."""

    return IToolResponse(
        **await start_calculation(
            job_type=JobType.catchment_area_active_mobility,
            tool_class=CRUDCatchmentAreaActiveMobility,
            crud_method="run_catchment_area",
            async_session=common.async_session,
            user_id=common.user_id,
            background_tasks=common.background_tasks,
            project_id=common.project_id,
            params=params,
            http_client=get_http_client(),
        )
    )


@router.post(
    "/heatmap-gravity",
    summary="Compute heatmap gravity for active mobility",
    response_model=IToolResponse,
    status_code=201,
    dependencies=[Depends(auth_z)],
)
async def compute_active_mobility_heatmap_gravity(
    *,
    common: CommonToolParams = Depends(),
    params: IHeatmapGravityActive = Body(
        ...,
        description="The heatmap gravity parameters.",
    ),
) -> IToolResponse:
    """Compute heatmap gravity for active mobility."""

    return IToolResponse(
        **await start_calculation(
            job_type=JobType.heatmap_gravity_active_mobility,
            tool_class=CRUDHeatmapGravity,
            crud_method="run_heatmap",
            async_session=common.async_session,
            user_id=common.user_id,
            background_tasks=common.background_tasks,
            project_id=common.project_id,
            params=params,
        )
    )


@router.post(
    "/heatmap-closest-average",
    summary="Compute heatmap closest-average for active mobility",
    response_model=IToolResponse,
    status_code=201,
    dependencies=[Depends(auth_z)],
)
async def compute_active_mobility_heatmap_closest_average(
    *,
    common: CommonToolParams = Depends(),
    params: IHeatmapClosestAverageActive = Body(
        ...,
        description="The heatmap closest-average parameters.",
    ),
) -> IToolResponse:
    """Compute heatmap closest-average for active mobility."""

    return IToolResponse(
        **await start_calculation(
            job_type=JobType.heatmap_closest_average_active_mobility,
            tool_class=CRUDHeatmapClosestAverage,
            crud_method="run_heatmap",
            async_session=common.async_session,
            user_id=common.user_id,
            background_tasks=common.background_tasks,
            project_id=common.project_id,
            params=params,
        )
    )


@router.post(
    "/heatmap-connectivity",
    summary="Compute heatmap connectivity for active mobility",
    response_model=IToolResponse,
    status_code=201,
    dependencies=[Depends(auth_z)],
)
async def compute_active_mobility_heatmap_connectivity(
    *,
    common: CommonToolParams = Depends(),
    params: IHeatmapConnectivityActive = Body(
        ...,
        description="The heatmap connectivity parameters.",
    ),
) -> IToolResponse:
    """Compute heatmap connectivity for active mobility."""

    return IToolResponse(
        **await start_calculation(
            job_type=JobType.heatmap_connectivity_active_mobility,
            tool_class=CRUDHeatmapConnectivity,
            crud_method="run_heatmap",
            async_session=common.async_session,
            user_id=common.user_id,
            background_tasks=common.background_tasks,
            project_id=common.project_id,
            params=params,
        )
    )
