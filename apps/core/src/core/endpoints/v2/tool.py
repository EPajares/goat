from fastapi import APIRouter, Body, Depends

from core.core.tool import CRUDToolBase, start_calculation
from core.crud.crud_data_management import CRUDJoin
from core.crud.crud_geoanalysis import (
    CRUDAggregatePoint,
    CRUDAggregatePolygon,
    CRUDOriginDestination,
)
from core.crud.crud_geoprocessing import CRUDBuffer
from core.deps.auth import auth_z
from core.schemas.error import http_error_handler
from core.schemas.job import JobType, Msg
from core.schemas.tool import (
    IAggregationPoint,
    IAggregationPolygon,
    IBuffer,
    IJoin,
    IOriginDestination,
    request_example_buffer,
    request_examples_aggregation_point,
    request_examples_aggregation_polygon,
    request_examples_join,
)
from core.schemas.toolbox_base import (
    CommonToolParams,
    IToolResponse,
    ToolsWithReferenceAreaCheck,
)

router = APIRouter()


@router.post(
    "/check-reference-area",
    summary="Check reference area",
    response_model=Msg,
    status_code=200,
    dependencies=[Depends(auth_z)],
)
async def check_reference_area(
    common: CommonToolParams = Depends(),
    layer_project_id: int = Body(
        ...,
        title="Layer Project ID",
        description="The ID of the layer project.",
    ),
    tool_type: ToolsWithReferenceAreaCheck = Body(
        ...,
        title="Tool Type",
        description="The type of the tool.",
    ),
) -> Msg:
    """Check if the reference area is suitable for the requested tool operation."""
    # Catch exception nand return HTTP error message
    crud_tool_base = CRUDToolBase(
        job_id=None,
        background_tasks=common.background_tasks,
        async_session=common.async_session,
        user_id=common.user_id,
        project_id=common.project_id,
    )
    # Excute and handle exception
    result = await http_error_handler(
        crud_tool_base.check_reference_area,
        layer_project_id=layer_project_id,
        tool_type=tool_type,
    )
    return Msg(text=result["msg"])


@router.post(
    "/join",
    summary="Join two layers.",
    response_model=IToolResponse,
    status_code=201,
    dependencies=[Depends(auth_z)],
)
async def join(
    common: CommonToolParams = Depends(),
    params: IJoin = Body(
        ...,
        example=request_examples_join,
        description="The join paramaters.",
    ),
) -> IToolResponse:
    """Join two layers based on a matching column and create a new layer containing the attributes of the target layer and the new column for the statistics results."""

    return IToolResponse(
        **await start_calculation(
            job_type=JobType.join,
            tool_class=CRUDJoin,
            crud_method="join_run",
            async_session=common.async_session,
            user_id=common.user_id,
            background_tasks=common.background_tasks,
            project_id=common.project_id,
            params=params,
        )
    )


@router.post(
    "/aggregate-points",
    summary="Aggregate points",
    response_model=IToolResponse,
    status_code=201,
    dependencies=[Depends(auth_z)],
)
async def aggregate_points(
    *,
    common: CommonToolParams = Depends(),
    params: IAggregationPoint = Body(
        ...,
        example=request_examples_aggregation_point,
        description="The aggregation parameters.",
    ),
) -> IToolResponse:
    """Aggregate points and compute statistics on a group by column."""
    return IToolResponse(
        **await start_calculation(
            job_type=JobType.aggregate_point,
            tool_class=CRUDAggregatePoint,
            crud_method="aggregate_point_run",
            async_session=common.async_session,
            user_id=common.user_id,
            background_tasks=common.background_tasks,
            project_id=common.project_id,
            params=params,
        )
    )


@router.post(
    "/aggregate-polygons",
    summary="Aggregate polygons",
    response_model=IToolResponse,
    status_code=201,
    dependencies=[Depends(auth_z)],
)
async def aggregate_polygons(
    *,
    common: CommonToolParams = Depends(),
    params: IAggregationPolygon = Body(
        ...,
        example=request_examples_aggregation_polygon,
        description="The aggregation parameters.",
    ),
) -> IToolResponse:
    """Aggregate polygons and compute statistics on a group by column."""
    return IToolResponse(
        **await start_calculation(
            job_type=JobType.aggregate_polygon,
            tool_class=CRUDAggregatePolygon,
            crud_method="aggregate_polygon_run",
            async_session=common.async_session,
            user_id=common.user_id,
            background_tasks=common.background_tasks,
            project_id=common.project_id,
            params=params,
        )
    )


@router.post(
    "/buffer",
    summary="Buffer",
    response_model=IToolResponse,
    status_code=201,
    dependencies=[Depends(auth_z)],
)
async def buffer(
    *,
    common: CommonToolParams = Depends(),
    params: IBuffer = Body(
        ...,
        example=request_example_buffer,
        description="The buffer parameters.",
    ),
) -> IToolResponse:
    """Buffer points and compute statistics on a group by column."""
    return IToolResponse(
        **await start_calculation(
            job_type=JobType.buffer,
            tool_class=CRUDBuffer,
            crud_method="buffer_run",
            async_session=common.async_session,
            user_id=common.user_id,
            background_tasks=common.background_tasks,
            project_id=common.project_id,
            params=params,
        )
    )


@router.post(
    "/origin-destination",
    summary="Origin Destination",
    response_model=IToolResponse,
    status_code=201,
    dependencies=[Depends(auth_z)],
)
async def origin_destination(
    *,
    common: CommonToolParams = Depends(),
    params: IOriginDestination = Body(
        ...,
        description="The origin destination parameters.",
    ),
) -> IToolResponse:
    """Create origin destination matrix."""
    return IToolResponse(
        **await start_calculation(
            job_type=JobType.origin_destination,
            tool_class=CRUDOriginDestination,
            crud_method="origin_destination_run",
            async_session=common.async_session,
            user_id=common.user_id,
            background_tasks=common.background_tasks,
            project_id=common.project_id,
            params=params,
        )
    )
