import logging
from uuid import UUID

import aiohttp
from sqlalchemy.ext.asyncio import AsyncSession

from core.core.config import settings
from core.db.models.folder import Folder
from core.db.models.layer import LayerType
from core.schemas.error import FolderNotFoundError
from core.schemas.folder import FolderCreate, FolderUpdate

from .base import CRUDBase

logger = logging.getLogger(__name__)


async def _delete_layers_via_geoapi(
    layer_ids: list[str], user_id: str, access_token: str
) -> None:
    """Delete layers via GeoAPI layer_delete_multi process.

    This triggers a single Windmill job to delete DuckLake tables for all layers.
    Runs as a background task after folder deletion from PostgreSQL.

    Args:
        layer_ids: List of layer UUIDs to delete
        user_id: User ID (owner of the layers)
        access_token: Bearer token for authentication
    """
    if not layer_ids:
        return

    if not settings.GOAT_GEOAPI_HOST:
        logger.warning(
            "GOAT_GEOAPI_HOST not configured, skipping DuckLake cleanup for %d layers",
            len(layer_ids),
        )
        return

    geoapi_url = f"{settings.GOAT_GEOAPI_HOST}/processes/layer_delete_multi/execution"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }

    async with aiohttp.ClientSession() as session:
        try:
            payload = {"inputs": {"layer_ids": layer_ids}}
            async with session.post(
                geoapi_url, json=payload, headers=headers
            ) as response:
                if response.status in (200, 201):
                    result = await response.json()
                    job_id = result.get("jobID", "unknown")
                    logger.info(
                        "Submitted layer_delete_multi job %s for %d layers",
                        job_id,
                        len(layer_ids),
                    )
                else:
                    error_text = await response.text()
                    logger.warning(
                        "Failed to submit layer_delete_multi for %d layers: %s %s",
                        len(layer_ids),
                        response.status,
                        error_text,
                    )
        except Exception as e:
            logger.warning(
                "Error submitting layer_delete_multi for %d layers: %s",
                len(layer_ids),
                e,
            )


class CRUDFolder(CRUDBase[Folder, FolderCreate, FolderUpdate]):
    async def delete(
        self,
        async_session: AsyncSession,
        *,
        id: UUID,
        user_id: UUID,
        access_token: str,
    ) -> None:
        db_obj = await self.get_by_multi_keys(
            async_session,
            keys={"id": id, "user_id": user_id},
            extra_fields=[Folder.layers],
        )
        # Check if folder exists
        if len(db_obj) == 0:
            raise FolderNotFoundError("Folder not found")

        folder_obj = db_obj[0]

        # Collect layer IDs that have DuckLake tables (feature and table layers)
        ducklake_layer_ids: list[str] = []
        if folder_obj.layers:
            for layer in folder_obj.layers:
                # Only feature and table layers have DuckLake tables
                if layer.type in [LayerType.feature, LayerType.table]:
                    ducklake_layer_ids.append(str(layer.id))

        # Remove folder from PostgreSQL (cascades to layer records)
        await self.remove(async_session, id=folder_obj.id)

        # Delete DuckLake tables via GeoAPI (awaited so job appears immediately)
        if ducklake_layer_ids:
            logger.info(
                "Deleting DuckLake data for %d layers from folder %s via GeoAPI",
                len(ducklake_layer_ids),
                id,
            )
            await _delete_layers_via_geoapi(
                ducklake_layer_ids,
                str(user_id),
                access_token,
            )


folder = CRUDFolder(Folder)
