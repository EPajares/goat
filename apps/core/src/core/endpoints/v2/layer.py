# Standard Libraries
import os
from typing import Any, Dict, Optional
from uuid import UUID

# Third-party Libraries
from fastapi import (
    APIRouter,
    BackgroundTasks,
    Body,
    Depends,
    HTTPException,
    Path,
    Query,
    Request,
    status,
)
from fastapi.responses import JSONResponse
from fastapi_pagination import Page
from fastapi_pagination import Params as PaginationParams
from pydantic import UUID4, BaseModel
from sqlmodel import SQLModel, select

from core.core.config import settings

# Local application imports
from core.core.content import (
    read_content_by_id,
)
from core.crud.crud_job import job as crud_job
from core.crud.crud_layer import layer as crud_layer
from core.crud.crud_layer_ducklake import (
    CRUDLayerExportDuckLake,
    CRUDLayerImportDuckLake,
    delete_layer_ducklake,
)
from core.db.models._link_model import LayerProjectLink
from core.db.models.layer import (
    FileUploadType,
    Layer,
    LayerType,
)
from core.db.models.project import ProjectPublic
from core.db.session import AsyncSession
from core.deps.auth import auth_z, auth_z_lite
from core.endpoints.deps import get_db, get_user_id
from core.schemas.common import OrderEnum
from core.schemas.error import HTTPErrorHandler
from core.schemas.job import JobType
from core.schemas.layer import (
    ICatalogLayerGet,
    IFeatureStandardLayerRead,
    IFeatureStreetNetworkLayerRead,
    IFeatureToolLayerRead,
    ILayerExport,
    ILayerFromDatasetCreate,
    ILayerGet,
    ILayerRead,
    IMetadataAggregate,
    IMetadataAggregateRead,
    IRasterCreate,
    IRasterLayerRead,
    ITableLayerRead,
)
from core.schemas.layer import (
    request_examples as layer_request_examples,
)
from core.services.s3 import s3_service

router = APIRouter()


async def _create_layer_from_dataset(
    background_tasks: BackgroundTasks,
    async_session: AsyncSession,
    user_id: UUID,
    project_id: Optional[UUID] = None,
    layer_in: ILayerFromDatasetCreate = Body(...),
) -> Dict[str, Any]:
    """Create a feature or table layer from S3 file or WFS service.

    The layer type (feature vs table) is auto-detected based on whether
    the data contains geometry.

    Supports two import modes:
    - S3: Import from a file previously uploaded to S3 (s3_key required)
    - WFS: Import directly from a WFS service (data_type=wfs, other_properties.url required)

    Returns a job_id that can be used to track the import progress.
    """
    from core.db.models.layer import FeatureDataType

    # Determine import mode: WFS or S3
    is_wfs = (
        layer_in.data_type == FeatureDataType.wfs
        and layer_in.other_properties is not None
        and layer_in.other_properties.url is not None
    )

    # --- Create job for tracking import progress
    job = await crud_job.check_and_create(
        async_session=async_session,
        user_id=user_id,
        job_type=JobType.file_import,
        project_id=project_id,
    )

    crud_import = CRUDLayerImportDuckLake(
        job_id=job.id,
        background_tasks=background_tasks,
        async_session=async_session,
        user_id=user_id,
    )

    if is_wfs:
        # --- WFS import: fetch directly from WFS service
        wfs_url = layer_in.other_properties.url
        wfs_layer_name = (
            layer_in.other_properties.layers[0]
            if layer_in.other_properties.layers
            else None
        )

        await crud_import.import_from_wfs_job(
            wfs_url=wfs_url,
            layer_in=layer_in,
            wfs_layer_name=wfs_layer_name,
            project_id=project_id,
        )
    else:
        # --- S3 import: read from previously uploaded file
        if layer_in.s3_key is None:
            raise HTTPException(400, "Missing required s3_key for file import")

        # Validate S3 key belongs to this user
        expected_prefix = s3_service.build_s3_key(
            settings.S3_BUCKET_PATH, "users", str(user_id), "imports"
        )
        if not layer_in.s3_key.startswith(expected_prefix):
            raise HTTPException(403, "Invalid s3_key (not owned by user)")

        # Validate file type
        orig_filename = os.path.basename(layer_in.s3_key)
        file_ext = os.path.splitext(orig_filename)[-1].lower()
        ext_trimmed = file_ext.lstrip(".")

        if ext_trimmed not in FileUploadType.__members__:
            raise HTTPException(
                415,
                f"File type not allowed. Allowed: {', '.join(FileUploadType.__members__.keys())}",
            )

        await crud_import.import_from_s3_job(
            s3_key=layer_in.s3_key,
            layer_in=layer_in,
            project_id=project_id,
        )

    return {"job_id": str(job.id)}


@router.post(
    "/internal",
    summary="Create a new layer (auto-detects feature vs table)",
    response_class=JSONResponse,
    status_code=202,
    description="Create a new layer from S3 file or WFS service. "
    "The layer type (feature or table) is automatically detected based on geometry. "
    "For S3: provide s3_key. For WFS: set data_type='wfs' and provide URL in other_properties.",
    dependencies=[Depends(auth_z)],
)
async def create_layer(
    background_tasks: BackgroundTasks,
    async_session: AsyncSession = Depends(get_db),
    user_id: UUID = Depends(get_user_id),
    project_id: Optional[UUID] = Query(
        None,
        description="The ID of the project to add the layer to",
        example="3fa85f64-5717-4562-b3fc-2c963f66afa6",
    ),
    layer_in: ILayerFromDatasetCreate = Body(
        ...,
        example=layer_request_examples["create"],
        description="Layer to create",
    ),
) -> Dict[str, Any]:
    """Create a new layer from S3 file or WFS service.

    Supports two import modes:
    - **S3 file**: Provide `s3_key` pointing to a previously uploaded file
    - **WFS service**: Set `data_type="wfs"` and provide WFS URL in `other_properties.url`

    The layer type is auto-detected based on geometry presence.

    Returns a job_id that can be used to track the import progress.
    """
    return await _create_layer_from_dataset(
        background_tasks=background_tasks,
        async_session=async_session,
        user_id=user_id,
        project_id=project_id,
        layer_in=layer_in,
    )


@router.post(
    "/raster",
    summary="Create a new raster layer",
    response_model=IRasterLayerRead,
    status_code=201,
    description="Generate a new layer based on a URL for a raster service hosted externally.",
    dependencies=[Depends(auth_z)],
)
async def create_layer_raster(
    async_session: AsyncSession = Depends(get_db),
    user_id: UUID4 = Depends(get_user_id),
    layer_in: IRasterCreate = Body(
        ...,
        example=layer_request_examples["create"],
        description="Layer to create",
    ),
) -> BaseModel:
    """Create a new raster layer from a service hosted externally."""

    layer = IRasterLayerRead(
        **(
            await crud_layer.create(
                db=async_session,
                obj_in=Layer(**layer_in.model_dump(), user_id=user_id).model_dump(),
            )
        ).model_dump()
    )
    return layer


@router.post(
    "/{layer_id}/export",
    summary="Export a layer to a file (async)",
    response_class=JSONResponse,
    status_code=202,
    description="Start an async export job. Returns a job_id to track progress. "
    "Once complete, use the job result's s3_key with the download endpoint.",
)
async def export_layer(
    background_tasks: BackgroundTasks,
    request: Request,
    async_session: AsyncSession = Depends(get_db),
    user_id: UUID4 = Depends(get_user_id),
    layer_id: UUID4 = Path(
        ...,
        description="The ID of the layer to export",
        example="3fa85f64-5717-4562-b3fc-2c963f66afa6",
    ),
    layer_in: ILayerExport = Body(
        ...,
        example=layer_request_examples["export"],
        description="Layer to export",
    ),
) -> Dict[str, Any]:
    """Export a layer to a file asynchronously.

    This endpoint starts a background export job and returns immediately with a job_id.
    The export runs asynchronously to avoid blocking the API.

    To get the exported file:
    1. Poll the job status endpoint with the returned job_id
    2. Once status is 'finished', get the s3_key from the job result
    3. Use the download endpoint with the s3_key to get a presigned URL

    Returns:
        job_id: UUID to track the export progress
    """
    # Check authorization status
    try:
        await auth_z_lite(request, async_session)
    except HTTPException:
        public_layer = (
            select(LayerProjectLink)
            .join(
                ProjectPublic,
                LayerProjectLink.project_id == ProjectPublic.project_id,
            )
            .where(
                LayerProjectLink.layer_id == layer_id,
            )
            .limit(1)
        )
        result = await async_session.execute(public_layer)
        public_layer = result.scalars().first()
        # Check if layer is public
        if not public_layer:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized"
            )

    # Create job for tracking export progress
    job = await crud_job.check_and_create(
        async_session=async_session,
        user_id=user_id,
        job_type=JobType.file_export,
    )

    # Run the export using DuckLake CRUD as background job
    crud_export = CRUDLayerExportDuckLake(
        job_id=job.id,
        background_tasks=background_tasks,
        async_session=async_session,
        user_id=user_id,
        layer_id=layer_id,
    )

    with HTTPErrorHandler():
        await crud_export.export_to_file_job(
            output_format=layer_in.file_type.value,
            file_name=layer_in.file_name,
            target_crs=layer_in.crs,
            where_clause=layer_in.query,
        )

    return {"job_id": str(job.id)}


@router.get(
    "/{layer_id}",
    summary="Retrieve a layer by its ID",
    response_model=ILayerRead,
    response_model_exclude_none=True,
    status_code=200,
    dependencies=[Depends(auth_z)],
)
async def read_layer(
    async_session: AsyncSession = Depends(get_db),
    layer_id: UUID4 = Path(
        ...,
        description="The ID of the layer to get",
        example="3fa85f64-5717-4562-b3fc-2c963f66afa6",
    ),
) -> SQLModel:
    """Retrieve a layer by its ID."""
    return await read_content_by_id(
        async_session=async_session, id=layer_id, model=Layer, crud_content=crud_layer
    )


@router.post(
    "",
    response_model=Page[ILayerRead],
    response_model_exclude_none=True,
    status_code=200,
    summary="Retrieve a list of layers using different filters including a spatial filter. If not filter is specified, all layers will be returned.",
    dependencies=[Depends(auth_z)],
)
async def read_layers(
    async_session: AsyncSession = Depends(get_db),
    page_params: PaginationParams = Depends(),
    user_id: UUID4 = Depends(get_user_id),
    obj_in: ILayerGet = Body(
        None,
        description="Layer to get",
    ),
    team_id: UUID | None = Query(
        None,
        description="The ID of the team to get the layers from",
        example="3fa85f64-5717-4562-b3fc-2c963f66afa6",
    ),
    organization_id: UUID | None = Query(
        None,
        description="The ID of the organization to get the layers from",
        example="3fa85f64-5717-4562-b3fc-2c963f66afa6",
    ),
    order_by: str = Query(
        None,
        description="Specify the column name that should be used to order. You can check the Layer model to see which column names exist.",
        example="created_at",
    ),
    order: OrderEnum = Query(
        "descendent",
        description="Specify the order to apply. There are the option ascendent or descendent.",
        example="descendent",
    ),
) -> Page:
    """This endpoints returns a list of layers based one the specified filters."""

    with HTTPErrorHandler():
        # Make sure that team_id and organization_id are not both set
        if team_id is not None and organization_id is not None:
            raise ValueError("Only one of team_id and organization_id can be set.")

        # Get layers from CRUD
        layers = await crud_layer.get_layers_with_filter(
            async_session=async_session,
            user_id=user_id,
            params=obj_in,
            order_by=order_by,
            order=order,
            page_params=page_params,
            team_id=team_id,
            organization_id=organization_id,
        )

    return layers


@router.post(
    "/catalog",
    response_model=Page[ILayerRead],
    response_model_exclude_none=True,
    status_code=200,
    summary="Retrieve a list of layers using different filters including a spatial filter. If not filter is specified, all layers will be returned.",
    dependencies=[Depends(auth_z)],
)
async def read_catalog_layers(
    async_session: AsyncSession = Depends(get_db),
    page_params: PaginationParams = Depends(),
    user_id: UUID4 = Depends(get_user_id),
    obj_in: ICatalogLayerGet = Body(
        None,
        description="Layer to get",
    ),
    order_by: str = Query(
        None,
        description="Specify the column name that should be used to order. You can check the Layer model to see which column names exist.",
        example="created_at",
    ),
    order: OrderEnum = Query(
        "descendent",
        description="Specify the order to apply. There are the option ascendent or descendent.",
        example="descendent",
    ),
) -> Page:
    """This endpoints returns a list of layers based one the specified filters."""

    with HTTPErrorHandler():
        # Get layers from CRUD
        layers = await crud_layer.get_layers_with_filter(
            async_session=async_session,
            user_id=user_id,
            params=obj_in,
            order_by=order_by,
            order=order,
            page_params=page_params,
        )

    return layers


@router.put(
    "/{layer_id}",
    response_model=ILayerRead,
    response_model_exclude_none=True,
    status_code=200,
    dependencies=[Depends(auth_z)],
)
async def update_layer(
    async_session: AsyncSession = Depends(get_db),
    layer_id: UUID4 = Path(
        ...,
        description="The ID of the layer to get",
        example="3fa85f64-5717-4562-b3fc-2c963f66afa6",
    ),
    layer_in: Dict[Any, Any] = Body(
        ..., example=layer_request_examples["update"], description="Layer to update"
    ),
) -> ILayerRead:
    with HTTPErrorHandler():
        result: SQLModel = await crud_layer.update(
            async_session=async_session,
            id=layer_id,
            layer_in=layer_in,
        )
        assert type(result) is (
            IFeatureStandardLayerRead
            | IFeatureStreetNetworkLayerRead
            | IFeatureToolLayerRead
            | ITableLayerRead
            | IRasterLayerRead
        )

    return result


@router.put(
    "/{layer_id}/dataset",
    response_class=JSONResponse,
    status_code=200,
    dependencies=[Depends(auth_z)],
)
async def update_layer_dataset(
    background_tasks: BackgroundTasks,
    async_session: AsyncSession = Depends(get_db),
    user_id: UUID = Depends(get_user_id),
    layer_id: UUID4 = Path(
        ...,
        description="The ID of the layer to update",
        example="3fa85f64-5717-4562-b3fc-2c963f66afa6",
    ),
    s3_key: str | None = Query(
        None, description="The S3 key of the dataset to update the layer with"
    ),
    refresh_wfs: bool = Query(
        False, description="If true, refresh WFS layer from its source URL"
    ),
) -> Dict[str, UUID]:
    """Update the dataset of a layer.

    Supports two modes:
    - **WFS refresh**: Set refresh_wfs=true to re-fetch from original WFS source
    - **S3 file**: Provide s3_key for a new file upload
    """
    from core.db.models.layer import FeatureDataType

    # Retrieve existing layer and authorize
    existing_layer = await crud_layer.get_internal(
        async_session=async_session,
        id=layer_id,
    )
    if str(existing_layer.user_id) != str(user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User does not have permission to update this layer.",
        )

    # Create job
    job = await crud_job.check_and_create(
        async_session=async_session,
        user_id=user_id,
        job_type=JobType.update_layer_dataset,
    )

    # Prepare layer_in for update
    layer_in = ILayerFromDatasetCreate(
        id=existing_layer.id,  # Keep same ID
        name=existing_layer.name,
        description=existing_layer.description,
        folder_id=existing_layer.folder_id,
        properties=existing_layer.properties,
        data_type=existing_layer.data_type,
        url=existing_layer.url,
        other_properties=existing_layer.other_properties,
        s3_key=s3_key,
    )

    crud_import = CRUDLayerImportDuckLake(
        job_id=job.id,
        background_tasks=background_tasks,
        async_session=async_session,
        user_id=user_id,
    )

    # WFS refresh: re-fetch from original WFS URL
    if refresh_wfs:
        if existing_layer.data_type != FeatureDataType.wfs:
            raise HTTPException(400, "Layer is not a WFS layer")
        if (
            not existing_layer.other_properties
            or not existing_layer.other_properties.get("url")
        ):
            raise HTTPException(400, "WFS layer has no source URL")

        wfs_url = existing_layer.other_properties["url"]
        wfs_layer_name = (
            existing_layer.other_properties.get("layers", [None])[0]
            if existing_layer.other_properties.get("layers")
            else None
        )

        # Delete old data first, then import fresh
        await delete_layer_ducklake(async_session, existing_layer)

        await crud_import.import_from_wfs_job(
            wfs_url=wfs_url,
            layer_in=layer_in,
            wfs_layer_name=wfs_layer_name,
            project_id=None,
        )

    # S3 file update
    elif s3_key:
        expected_prefix = s3_service.build_s3_key(
            settings.S3_BUCKET_PATH, "users", str(user_id), "imports"
        )
        if not s3_key.startswith(expected_prefix):
            raise HTTPException(403, "Invalid s3_key (not owned by user)")

        # Validate file type
        orig_filename = os.path.basename(s3_key)
        file_ext = os.path.splitext(orig_filename)[-1].lower().lstrip(".")
        if file_ext not in FileUploadType.__members__:
            raise HTTPException(
                415,
                f"File type not allowed. Allowed: {', '.join(FileUploadType.__members__.keys())}",
            )

        # Delete old data first, then import fresh
        await delete_layer_ducklake(async_session, existing_layer)

        await crud_import.import_from_s3_job(
            s3_key=s3_key,
            layer_in=layer_in,
            project_id=None,
        )

    else:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            "You must provide one of: refresh_wfs=true or s3_key",
        )

    return {"job_id": job.id}


@router.delete(
    "/{layer_id}",
    response_model=None,
    summary="Delete a layer and its data in case of an internal layer.",
    status_code=204,
    dependencies=[Depends(auth_z)],
)
async def delete_layer(
    async_session: AsyncSession = Depends(get_db),
    layer_id: UUID4 = Path(
        ...,
        description="The ID of the layer to get",
        example="3fa85f64-5717-4562-b3fc-2c963f66afa6",
    ),
) -> None:
    """Delete a layer and its data in case of an internal layer."""

    with HTTPErrorHandler():
        # Get layer first to check type and get user_id
        layer = await crud_layer.get_internal(
            async_session=async_session,
            id=layer_id,
        )

        # Delete DuckLake data for feature/table layers
        if layer.type in (LayerType.feature, LayerType.table):
            await delete_layer_ducklake(
                async_session=async_session,
                layer=layer,
            )

        # Delete layer metadata from PostgreSQL
        await crud_layer.delete(
            async_session=async_session,
            id=layer_id,
        )
    return


@router.post(
    "/metadata/aggregate",
    summary="Return the count of layers for different metadata values acting as filters",
    response_model=IMetadataAggregateRead,
    status_code=200,
    dependencies=[Depends(auth_z)],
)
async def metadata_aggregate(
    async_session: AsyncSession = Depends(get_db),
    user_id: UUID4 = Depends(get_user_id),
    obj_in: IMetadataAggregate = Body(
        None,
        description="Filter for metadata to aggregate",
    ),
) -> IMetadataAggregateRead:
    """Return the count of layers for different metadata values acting as filters."""
    with HTTPErrorHandler():
        result = await crud_layer.metadata_aggregate(
            async_session=async_session,
            user_id=user_id,
            params=obj_in,
        )
    return result
