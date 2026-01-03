import json

from fastapi import APIRouter, Body
from fastapi.responses import JSONResponse, Response
from routing.core.config import settings
from routing.crud.crud_catchment_area import CRUDCatchmentArea
from routing.db.session import async_session
from routing.schemas.catchment_area import (
    ICatchmentAreaActiveMobility,
    ICatchmentAreaCar,
    OutputFormat,
    request_examples,
)
from routing.schemas.error import DisconnectedOriginError

router = APIRouter()

# Shared CRUD instance for caching routing network
_crud_catchment_area: CRUDCatchmentArea | None = None


def get_crud_catchment_area() -> CRUDCatchmentArea:
    """Get or create CRUD catchment area instance with cached routing network."""
    global _crud_catchment_area
    if _crud_catchment_area is None:
        _crud_catchment_area = CRUDCatchmentArea(async_session(), redis=None)
    return _crud_catchment_area


@router.post(
    "/active-mobility/catchment-area",
    summary="Compute catchment areas for active mobility",
    response_model=None,
)
async def compute_active_mobility_catchment_area(
    *,
    params: ICatchmentAreaActiveMobility = Body(
        ...,
        examples=request_examples["catchment_area_active_mobility"],
        description="The catchment area parameters.",
    ),
):
    """Compute catchment areas for active mobility."""

    return await compute_catchment_area(params)


@router.post(
    "/motorized-mobility/catchment-area",
    summary="Compute catchment areas for motorized mobility",
    response_model=None,
)
async def compute_motorized_mobility_catchment_area(
    *,
    params: ICatchmentAreaCar = Body(
        ...,
        examples=request_examples["catchment_area_motorized_mobility"],
        description="The catchment area parameters.",
    ),
):
    """Compute catchment areas for motorized mobility."""

    return await compute_catchment_area(params)


async def compute_catchment_area(
    params: ICatchmentAreaActiveMobility | ICatchmentAreaCar,
):
    """Compute catchment area and return results as GeoJSON or Parquet."""
    try:
        crud = get_crud_catchment_area()
        params_dict = json.loads(params.model_dump_json())
        result = await crud.run(params_dict)

        if result is None:
            return JSONResponse(
                content={
                    "error": "Failed to compute catchment area.",
                },
                status_code=500,
            )

        if params.output_format == OutputFormat.parquet:
            # Return Parquet bytes
            return Response(
                content=result,
                media_type="application/octet-stream",
                headers={
                    "Content-Disposition": "attachment; filename=catchment_area.parquet"
                },
            )
        else:
            # Return GeoJSON
            return JSONResponse(
                content=result,
                status_code=200,
            )

    except DisconnectedOriginError:
        return JSONResponse(
            content={
                "error": "Starting point(s) are disconnected from the street network.",
            },
            status_code=400,
        )
    except Exception as e:
        print(f"Error computing catchment area: {e}")
        return JSONResponse(
            content={
                "error": f"Failed to compute catchment area: {str(e)}",
            },
            status_code=500,
        )
