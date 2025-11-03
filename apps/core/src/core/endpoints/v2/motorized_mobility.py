from fastapi import APIRouter, Body, Depends

from core.core.tool import start_calculation
from core.crud.crud_catchment_area import (
    CRUDCatchmentAreaCar,
    CRUDCatchmentAreaPT,
)
from core.crud.crud_heatmap_closest_average import CRUDHeatmapClosestAverage
from core.crud.crud_heatmap_connectivity import CRUDHeatmapConnectivity
from core.crud.crud_heatmap_gravity import CRUDHeatmapGravity
from core.crud.crud_nearby_station_access import CRUDNearbyStationAccess
from core.crud.crud_oev_gueteklasse import CRUDOevGueteklasse
from core.crud.crud_trip_count_station import CRUDTripCountStation
from core.deps.auth import auth_z
from core.endpoints.deps import get_http_client
from core.schemas.catchment_area import (
    ICatchmentAreaCar,
    ICatchmentAreaPT,
    request_examples_catchment_area_car,
    request_examples_catchment_area_pt,
)
from core.schemas.heatmap import (
    IHeatmapClosestAverageMotorized,
    IHeatmapConnectivityMotorized,
    IHeatmapGravityMotorized,
)
from core.schemas.job import JobType
from core.schemas.nearby_station_access import (
    INearbyStationAccess,
    request_example_nearby_station_access,
)
from core.schemas.oev_gueteklasse import (
    IOevGueteklasse,
    request_example_oev_gueteklasse,
)
from core.schemas.toolbox_base import CommonToolParams, IToolResponse
from core.schemas.trip_count_station import ITripCountStation

router = APIRouter()


@router.post(
    "/pt/catchment-area",
    summary="Compute catchment areas for public transport.",
    response_model=IToolResponse,
    status_code=201,
    dependencies=[Depends(auth_z)],
)
async def compute_pt_catchment_area(
    *,
    common: CommonToolParams = Depends(),
    params: ICatchmentAreaPT = Body(
        ...,
        example=request_examples_catchment_area_pt,
        description="The catchment area parameters.",
    ),
) -> IToolResponse:
    """Compute catchment areas for public transport."""
    return IToolResponse(
        **await start_calculation(
            job_type=JobType.catchment_area_pt,
            tool_class=CRUDCatchmentAreaPT,
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
    "/car/catchment-area",
    summary="Compute catchment areas for car.",
    response_model=IToolResponse,
    status_code=201,
    dependencies=[Depends(auth_z)],
)
async def compute_car_catchment_area(
    *,
    common: CommonToolParams = Depends(),
    params: ICatchmentAreaCar = Body(
        ...,
        example=request_examples_catchment_area_car,
        description="The catchment area parameters.",
    ),
) -> IToolResponse:
    """Compute catchment areas for car."""
    return IToolResponse(
        **await start_calculation(
            job_type=JobType.catchment_area_car,
            tool_class=CRUDCatchmentAreaCar,
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
    "/oev-gueteklassen",
    summary="Calculate ÖV-Güteklassen.",
    response_model=IToolResponse,
    status_code=201,
    dependencies=[Depends(auth_z)],
)
async def compute_oev_gueteklassen(
    *,
    common: CommonToolParams = Depends(),
    params: IOevGueteklasse = Body(..., example=request_example_oev_gueteklasse),
) -> IToolResponse:
    """
    ÖV-Güteklassen (The public transport quality classes) is an indicator for access to public transport.
    The indicator makes it possible to identify locations which, thanks to their good access to public transport, have great potential as focal points for development.
    The calculation in an automated process from the data in the electronic timetable (GTFS).
    """

    return IToolResponse(
        **await start_calculation(
            job_type=JobType.oev_gueteklasse,
            tool_class=CRUDOevGueteklasse,
            crud_method="oev_gueteklasse_run",
            async_session=common.async_session,
            user_id=common.user_id,
            background_tasks=common.background_tasks,
            project_id=common.project_id,
            params=params,
        )
    )


@router.post(
    "/trip-count-station",
    summary="Calculate trip count per station.",
    response_model=IToolResponse,
    status_code=201,
    dependencies=[Depends(auth_z)],
)
async def compute_trip_count_station(
    *,
    common: CommonToolParams = Depends(),
    params: ITripCountStation = Body(..., example=request_example_oev_gueteklasse),
) -> IToolResponse:
    """Calculates the number of trips per station and public transport mode."""

    return IToolResponse(
        **await start_calculation(
            job_type=JobType.trip_count_station,
            tool_class=CRUDTripCountStation,
            crud_method="trip_count_run",
            async_session=common.async_session,
            user_id=common.user_id,
            background_tasks=common.background_tasks,
            project_id=common.project_id,
            params=params,
        )
    )


@router.post(
    "/nearby-station-access",
    summary="Get public transport stops and their trips that are accessible by walking/cycling.",
    response_model=IToolResponse,
    status_code=201,
    dependencies=[Depends(auth_z)],
)
async def compute_nearby_station_access(
    *,
    common: CommonToolParams = Depends(),
    params: INearbyStationAccess = Body(
        ...,
        example=request_example_nearby_station_access,
        description="The catchment area parameters.",
    ),
) -> IToolResponse:
    """Get public transport stops and their trips that are accessible by walking/cycling."""
    return IToolResponse(
        **await start_calculation(
            job_type=JobType.nearby_station_access,
            tool_class=CRUDNearbyStationAccess,
            crud_method="nearby_station_access_run",
            async_session=common.async_session,
            user_id=common.user_id,
            background_tasks=common.background_tasks,
            project_id=common.project_id,
            params=params,
        )
    )


@router.post(
    "/heatmap-gravity",
    summary="Compute heatmap gravity for motorized mobility",
    response_model=IToolResponse,
    status_code=201,
    dependencies=[Depends(auth_z)],
)
async def compute_motorized_mobility_heatmap_gravity(
    *,
    common: CommonToolParams = Depends(),
    params: IHeatmapGravityMotorized = Body(
        ...,
        description="The heatmap gravity parameters.",
    ),
) -> IToolResponse:
    """Compute heatmap gravity for motorized mobility."""

    return IToolResponse(
        **await start_calculation(
            job_type=JobType.heatmap_gravity_motorized_mobility,
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
    summary="Compute heatmap closest-average for motorized mobility",
    response_model=IToolResponse,
    status_code=201,
    dependencies=[Depends(auth_z)],
)
async def compute_motorized_mobility_heatmap_closest_average(
    *,
    common: CommonToolParams = Depends(),
    params: IHeatmapClosestAverageMotorized = Body(
        ...,
        description="The heatmap closest-average parameters.",
    ),
) -> IToolResponse:
    """Compute heatmap closest-average for motorized mobility."""

    return IToolResponse(
        **await start_calculation(
            job_type=JobType.heatmap_closest_average_motorized_mobility,
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
    summary="Compute heatmap connectivity for motorized mobility",
    response_model=IToolResponse,
    status_code=201,
    dependencies=[Depends(auth_z)],
)
async def compute_motorized_mobility_heatmap_connectivity(
    *,
    common: CommonToolParams = Depends(),
    params: IHeatmapConnectivityMotorized = Body(
        ...,
        description="The heatmap connectivity parameters.",
    ),
) -> IToolResponse:
    """Compute heatmap connectivity for motorized mobility."""

    return IToolResponse(
        **await start_calculation(
            job_type=JobType.heatmap_connectivity_motorized_mobility,
            tool_class=CRUDHeatmapConnectivity,
            crud_method="run_heatmap",
            async_session=common.async_session,
            user_id=common.user_id,
            background_tasks=common.background_tasks,
            project_id=common.project_id,
            params=params,
        )
    )
