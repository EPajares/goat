import mimetypes
import uuid
from io import BytesIO
from typing import List

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    Path,
    UploadFile,
    status,
)
from pydantic import UUID4
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from core.core.config import settings
from core.db.models.asset import AssetType, UploadedAsset
from core.deps.auth import auth_z
from core.endpoints.deps import get_db, get_user_id
from core.schemas.asset import AssetRead, AssetUpdate
from core.services.s3 import s3_service

router = APIRouter()

# Define allowed MIME types for each asset type
ALLOWED_MIME_TYPES = {
    AssetType.IMAGE: [
        "image/jpeg",
        "image/png",
        "image/gif",
        "image/webp",
        "image/bmp",
        "image/tiff",
        "image/svg+xml",
        "image/x-icon",
    ],
    AssetType.ICON: [
        "image/svg+xml",
        "image/jpeg",
        "image/webp",
        "image/x-icon",
        "image/bmp",
        "image/png",
    ],
}


@router.post(
    "/upload",
    response_model=AssetRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(auth_z)],
)
async def upload_asset(
    async_session: AsyncSession = Depends(get_db),
    user_id: UUID4 = Depends(get_user_id),
    file: UploadFile = File(...),
    asset_type: AssetType = Form(...),
    display_name: str | None = Form(None),
    category: str | None = Form(None),
) -> AssetRead:
    """
    Uploads a new asset to S3 and records its metadata in the database.
    - Only allows supported image/icon MIME types.
    - For `icon` assets, `display_name` and `category` are required.
    """

    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="No file selected."
        )

    # --- Enforce required fields for icons ---
    if asset_type == AssetType.ICON and not display_name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Both 'display_name' and 'category' are required for icon uploads.",
        )

    # 1. Validate MIME type
    detected_mime_type, _ = mimetypes.guess_type(file.filename)
    actual_mime_type = detected_mime_type or file.content_type
    if actual_mime_type not in ALLOWED_MIME_TYPES.get(asset_type, []):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Invalid file type for asset_type '{asset_type.value}'. "
                f"Allowed types: {', '.join(ALLOWED_MIME_TYPES.get(asset_type, []))}. "
                f"Received: {actual_mime_type}"
            ),
        )

    # 2. Read file + enforce size limit
    file_content = await file.read()
    if len(file_content) > settings.ASSETS_MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File too large. Maximum allowed size is {settings.ASSETS_MAX_FILE_SIZE // (1024 * 1024)} MB.",
        )

    # 3. Hash content and check if an identical asset exists (per user)
    content_hash = s3_service.calculate_sha256(file_content)
    existing_asset = await async_session.execute(
        select(UploadedAsset)
        .where(UploadedAsset.content_hash == content_hash)
        .where(UploadedAsset.user_id == user_id)
        .where(UploadedAsset.asset_type == asset_type)
    )
    existing_asset = existing_asset.fetchone()

    if existing_asset:
        existing_asset = existing_asset[0]
        # Update file_name if user re-uploads identical content with a different name
        existing_asset.file_name = file.filename
        existing_asset.display_name = display_name or existing_asset.display_name
        existing_asset.category = category or existing_asset.category
        async_session.add(existing_asset)
        await async_session.commit()
        await async_session.refresh(existing_asset)
        return existing_asset  # Return the existing record

    # 4. Prepare file for S3 upload
    file_extension = mimetypes.guess_extension(actual_mime_type)
    if not file_extension:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Could not determine file extension for MIME type '{actual_mime_type}'.",
        )

    s3_key = f"goat/{settings.ENVIRONMENT}/users/{user_id}/{asset_type.value}/{uuid.uuid4().hex}{file_extension}"
    s3_service.upload_file(
        BytesIO(file_content),
        settings.AWS_S3_ASSETS_BUCKET,
        s3_key,
        actual_mime_type,
    )

    # 5. Save metadata into DB
    new_asset = UploadedAsset(
        user_id=user_id,
        s3_key=s3_key,
        file_name=file.filename,
        mime_type=actual_mime_type,
        file_size=len(file_content),
        asset_type=asset_type,
        content_hash=content_hash,
        display_name=display_name,
        category=category,
    )
    async_session.add(new_asset)
    await async_session.commit()
    await async_session.refresh(new_asset)

    return AssetRead.model_validate(new_asset)


@router.get(
    "",
    summary="List all assets for the authenticated user",
    response_model=List[AssetRead],
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(auth_z)],
)
async def read_assets(
    async_session: AsyncSession = Depends(get_db),
    user_id: UUID4 = Depends(get_user_id),
    asset_type: AssetType | None = None,
) -> List[AssetRead]:
    query = select(UploadedAsset).where(UploadedAsset.user_id == user_id)

    if asset_type:
        query = query.where(UploadedAsset.asset_type == asset_type)

    result = await async_session.execute(query)
    assets = result.scalars().all()

    response = [AssetRead.model_validate(asset) for asset in assets]

    return response


@router.put(
    "/{asset_id}",
    response_model=AssetRead,
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(auth_z)],
    summary="Update asset metadata",
)
async def update_asset(
    asset_id: UUID4,
    asset_update: AssetUpdate,
    async_session: AsyncSession = Depends(get_db),
    user_id: UUID4 = Depends(get_user_id),
) -> AssetRead:
    # Fetch asset
    result = await async_session.execute(
        select(UploadedAsset)
        .where(UploadedAsset.id == asset_id)
        .where(UploadedAsset.user_id == user_id)
    )
    asset = result.scalar_one_or_none()
    if not asset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Asset not found",
        )

    # Update fields
    if asset_update.display_name is not None:
        asset.display_name = asset_update.display_name
    if asset_update.category is not None:
        asset.category = asset_update.category

    async_session.add(asset)
    await async_session.commit()
    await async_session.refresh(asset)

    return AssetRead.model_validate(asset)


@router.delete(
    "/{asset_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(auth_z)],
    summary="Delete an asset",
)
async def delete_asset(
    asset_id: UUID4 = Path(..., description="ID of the asset to delete"),
    async_session: AsyncSession = Depends(get_db),
    user_id: UUID4 = Depends(get_user_id),
) -> None:
    # Fetch asset
    result = await async_session.execute(
        select(UploadedAsset)
        .where(UploadedAsset.id == asset_id)
        .where(UploadedAsset.user_id == user_id)
    )
    asset = result.scalar_one_or_none()
    if not asset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Asset not found",
        )

    # Delete from S3
    try:
        s3_service.delete_file(settings.AWS_S3_ASSETS_BUCKET, asset.s3_key)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete asset from storage: {e}",
        )

    # Delete from DB
    await async_session.delete(asset)
    await async_session.commit()

    return None



