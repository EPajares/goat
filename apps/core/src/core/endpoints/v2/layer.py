# Standard Libraries
import json
import os
import tempfile
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
    UploadFile,
    logger,
    status,
)
from fastapi.responses import FileResponse, JSONResponse
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
from core.crud.crud_layer import (
    CRUDLayerDatasetUpdate,
)
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
    IFileUploadExternalService,
    IFileUploadMetadata,
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


@router.post(
    "/file-upload-external-service",
    summary="Fetch data from external service into a file, upload file to S3 and validate",
    response_model=IFileUploadMetadata,
    status_code=201,
    dependencies=[Depends(auth_z)],
)
async def file_upload_external_service(
    *,
    async_session: AsyncSession = Depends(get_db),
    user_id: UUID = Depends(get_user_id),
    external_service: IFileUploadExternalService = Body(
        ...,
        description="External service to fetch data from.",
    ),
) -> IFileUploadMetadata:
    """
    Fetch data from an external service, save to disk, upload to S3, then validate.
    """
    layer_type = LayerType.feature

    # 1. Run validation pipeline (fetch external → save locally → validate)
    metadata = await crud_layer.upload_file(
        async_session=async_session,
        user_id=user_id,
        source=external_service,
        layer_type=layer_type,
    )

    # 2. Upload validated file to S3
    try:
        # Open the validated local file
        with open(metadata.file_path, "rb") as f:
            s3_key = s3_service.build_s3_key(
                settings.S3_BUCKET_PATH,
                "users",
                str(user_id),
                "imports",
                "external",
                f"{metadata.dataset_id}_{os.path.basename(metadata.file_path)}",
            )
            s3_service.upload_file(
                file_content=f,
                bucket_name=settings.S3_BUCKET_NAME,
                s3_key=s3_key,
                content_type="application/octet-stream",
            )
            # 3. Add s3_key to metadata
            metadata.s3_key = s3_key
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to upload external service file to S3: {e}",
        )

    return metadata


def _validate_and_fetch_metadata(
    user_id: UUID,
    dataset_id: UUID,
) -> Dict[str, Any]:
    # Check if user owns folder by checking if it exists
    folder_path = os.path.join(settings.DATA_DIR, str(user_id), str(dataset_id))
    if os.path.exists(folder_path) is False:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dataset not found or not owned by user.",
        )

    # Get metadata from file in folder
    metadata_path = None
    for root, _dirs, files in os.walk(folder_path):
        if "metadata.json" in files:
            metadata_path = os.path.join(root, "metadata.json")

    if metadata_path is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Metadata file not found.",
        )

    with open(os.path.join(metadata_path)) as f:
        file_metadata = dict(json.loads(json.load(f)))

    return file_metadata


async def _create_layer_from_dataset(
    background_tasks: BackgroundTasks,
    async_session: AsyncSession,
    user_id: UUID,
    project_id: Optional[UUID] = None,
    layer_in: ILayerFromDatasetCreate = Body(...),
) -> Dict[str, UUID]:
    """Create a feature or table layer from a dataset uploaded to S3.

    The layer type (feature vs table) is auto-detected based on whether
    the data contains geometry. CSV/Excel with WKT geometry columns will
    automatically become feature layers.
    """

    # --- ensure s3 key belongs to this user
    expected_prefix = s3_service.build_s3_key(
        settings.S3_BUCKET_PATH, "users", str(user_id), "imports"
    )
    if layer_in.s3_key is None:
        raise HTTPException(400, "Missing required s3_key")

    if not layer_in.s3_key.startswith(expected_prefix):
        raise HTTPException(403, "Invalid s3_key (not owned by user)")

    # --- original filename from S3 key
    orig_filename = os.path.basename(layer_in.s3_key)
    file_ext = os.path.splitext(orig_filename)[-1].lower()
    ext_trimmed = file_ext.lstrip(".")

    # --- Validate file type is allowed (but don't pre-determine layer type)
    if ext_trimmed not in FileUploadType.__members__:
        raise HTTPException(
            415,
            f"File type not allowed. Allowed: {', '.join(FileUploadType.__members__.keys())}",
        )

    # --- Tmp directory for this user
    tmp_dir = os.path.join(tempfile.gettempdir(), str(user_id))
    os.makedirs(tmp_dir, exist_ok=True)
    tmp_path = os.path.join(tmp_dir, orig_filename)

    try:
        # --- Download from S3 to /tmp/{user_id}/{filename}
        s3_service.s3_client.download_file(
            settings.S3_BUCKET_NAME,
            layer_in.s3_key,
            tmp_path,
        )

        # --- Wrap downloaded file as UploadFile
        # Note: layer_type is not pre-determined here anymore
        # The actual type will be detected after goatlib conversion based on geometry
        with open(tmp_path, "rb") as f:
            upload = UploadFile(filename=orig_filename, file=f)

            # Use feature type for validation - goatlib will handle both
            # The actual layer type is determined during import based on geometry presence
            file_metadata = await crud_layer.upload_file(
                async_session=async_session,
                user_id=user_id,
                source=upload,
                layer_type=LayerType.feature,  # Default for validation, actual type determined by geometry
            )

    except Exception as e:
        raise HTTPException(500, f"Error handling file from S3: {e}")
    finally:
        # --- Always cleanup
        try:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
        except Exception as cleanup_err:
            # log, but don’t swallow main exception
            logger.warning(f"Could not delete temp file {tmp_path}: {cleanup_err}")

    # --- Run import directly (layer type auto-detected based on geometry)
    from uuid import uuid4

    job_id = uuid4()  # Dummy job_id for now
    crud_import = CRUDLayerImportDuckLake(
        job_id=job_id,
        background_tasks=background_tasks,
        async_session=async_session,
        user_id=user_id,
    )
    result, layer_id = await crud_import.import_file(
        file_path=file_metadata.file_path,
        layer_in=layer_in,
        file_metadata=file_metadata.model_dump(),
        project_id=project_id,
    )

    return {"layer_id": str(layer_id), **result}


@router.post(
    "/internal",
    summary="Create a new layer (auto-detects feature vs table)",
    response_class=JSONResponse,
    status_code=201,
    description="Create a new layer from a previously uploaded dataset. "
    "The layer type (feature or table) is automatically detected based on "
    "whether the data contains geometry. CSV/Excel files with WKT geometry "
    "columns will be imported as feature layers.",
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
    """Create a new layer from a previously uploaded dataset.

    The layer type is auto-detected:
    - Files with geometry (GeoJSON, GPKG, SHP, KML, or CSV/Excel with WKT column) → feature layer
    - Files without geometry (plain CSV, Excel) → table layer
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
    summary="Export a layer to a file",
    response_class=FileResponse,
    status_code=201,
    description="Export a layer to a zip file.",
)
async def export_layer(
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
) -> FileResponse:
    # Check authorization statusAdd commentMore actions
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
    # Run the export using DuckLake CRUD
    crud_export = CRUDLayerExportDuckLake(
        layer_id=layer_id,
        async_session=async_session,
        user_id=user_id,
    )
    with HTTPErrorHandler():
        zip_file_path = await crud_export.export_to_file(
            output_format=layer_in.file_type.value,
            file_name=layer_in.file_name,
            target_crs=layer_in.crs,
            where_clause=layer_in.query,
        )

    # Return file with cleanup after download
    file_name = os.path.basename(zip_file_path)
    user_export_dir = os.path.dirname(zip_file_path)  # data/{user_id}

    # Background task to delete the zip file and empty user folder after response
    async def cleanup_export_file() -> None:
        try:
            if os.path.exists(zip_file_path):
                os.remove(zip_file_path)
            # Also remove parent user folder if empty
            if user_export_dir and os.path.isdir(user_export_dir):
                try:
                    os.rmdir(user_export_dir)  # Only removes if empty
                except OSError:
                    pass  # Not empty, that's fine
        except Exception:
            pass  # Best effort cleanup

    background_tasks = BackgroundTasks()
    background_tasks.add_task(cleanup_export_file)

    return FileResponse(
        zip_file_path,
        media_type="application/zip",
        filename=file_name,
        background=background_tasks,
    )


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
    dataset_id: UUID | None = Query(
        None, description="The ID of the dataset to update the layer with"
    ),
    s3_key: str | None = Query(
        None, description="The S3 key of the dataset to update the layer with"
    ),
) -> Dict[str, UUID]:
    """Update the dataset of a layer. Either by dataset_id (legacy/external service) or by s3_key (S3 uploaded file)."""

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

    # 1Legacy / external service flow: dataset_id used
    if dataset_id and not s3_key:
        file_metadata = _validate_and_fetch_metadata(
            user_id=user_id,
            dataset_id=dataset_id,
        )

    # New S3 flow: s3_key provided
    elif s3_key and not dataset_id:
        expected_prefix = s3_service.build_s3_key(
            settings.S3_BUCKET_PATH, "users", str(user_id), "imports"
        )
        if not s3_key.startswith(expected_prefix):
            raise HTTPException(403, "Invalid s3_key (not owned by user)")

        orig_filename = os.path.basename(s3_key)
        file_ext = os.path.splitext(orig_filename)[-1].lower().lstrip(".")

        # Validate file type is allowed
        if file_ext not in FileUploadType.__members__:
            raise HTTPException(
                415,
                f"File type not allowed. Allowed: {', '.join(FileUploadType.__members__.keys())}",
            )

        # Download to tmp
        tmp_dir = os.path.join(tempfile.gettempdir(), str(user_id))
        os.makedirs(tmp_dir, exist_ok=True)
        tmp_path = os.path.join(tmp_dir, orig_filename)
        try:
            s3_service.s3_client.download_file(
                settings.S3_BUCKET_NAME,
                s3_key,
                tmp_path,
            )
            with open(tmp_path, "rb") as f:
                upload = UploadFile(filename=orig_filename, file=f)
                # Layer type is auto-detected based on geometry presence
                file_metadata = await crud_layer.upload_file(
                    async_session=async_session,
                    user_id=user_id,
                    source=upload,
                    layer_type=LayerType.feature,  # Default for validation
                )
        except Exception as e:
            raise HTTPException(500, f"Error handling file from S3: {e}")
        finally:
            try:
                if os.path.exists(tmp_path):
                    os.remove(tmp_path)
            except Exception as cleanup_err:
                logger.warning(f"Could not delete temp file {tmp_path}: {cleanup_err}")

        # If crud_layer.upload_file returns a Pydantic model, ensure dict
        if not isinstance(file_metadata, dict):
            file_metadata = file_metadata.model_dump()

    else:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            "You must pass either dataset_id or s3_key, but not both.",
        )

    # Create job
    job = await crud_job.check_and_create(
        async_session=async_session,
        user_id=user_id,
        job_type=JobType.update_layer_dataset,
    )

    # Prepare new layer_in
    layer_in = ILayerFromDatasetCreate(
        name=existing_layer.name,
        description=existing_layer.description,
        folder_id=existing_layer.folder_id,
        properties=existing_layer.properties,
        data_type=existing_layer.data_type,
        url=existing_layer.url,
        other_properties=existing_layer.other_properties,
        dataset_id=dataset_id,
        s3_key=s3_key,
        # s3_key could also be added to schema if you extend it
    )

    # Run dataset update
    await CRUDLayerDatasetUpdate(
        background_tasks=background_tasks,
        async_session=async_session,
        user_id=user_id,
        job_id=job.id,
    ).update(
        existing_layer_id=existing_layer.id,
        file_metadata=file_metadata,
        layer_in=layer_in,
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


# NOTE: The following analytics endpoints have been moved to GeoAPI OGC API Processes:
# - GET /{layer_id}/feature-count -> POST /processes/feature-count/execution
# - GET /{layer_id}/area/{operation} -> POST /processes/area-statistics/execution
# - GET /{layer_id}/unique-values/{column_name} -> POST /processes/unique-values/execution
# - GET /{layer_id}/class-breaks/{operation}/{column_name} -> POST /processes/class-breaks/execution


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
