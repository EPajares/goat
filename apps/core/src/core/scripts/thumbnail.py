import asyncio
from datetime import datetime, timezone
from uuid import uuid4

from core.core.config import settings
from core.core.print import PrintMap
from core.crud.base import CRUDBase
from core.crud.crud_layer_project import layer_project as crud_layer_project
from core.crud.crud_user_project import user_project as crud_user_project
from core.db.models.layer import Layer
from core.db.models.project import Project
from core.db.session import session_manager
from core.schemas.layer import FeatureType, LayerType
from core.scripts.utils import fetch_last_run_timestamp, update_last_run_timestamp
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

SYSTEM_TASK_ID = "thumbnail_update"


async def fetch_projects_to_update(
    async_session: AsyncSession, last_run: datetime
) -> list[Project]:
    """Fetch all projects which require a thumbnail update."""

    query = select(Project).where(Project.updated_at > last_run)
    return await CRUDBase(Project).get_multi(
        async_session,
        query=query,
    )


async def fetch_layers_to_update(
    async_session: AsyncSession, last_run: datetime
) -> list[Layer]:
    """Fetch all layers which require a thumbnail update."""

    query = select(Layer).where(Layer.updated_at > last_run)
    return await CRUDBase(Layer).get_multi(
        async_session,
        query=query,
    )


async def process_projects(async_session: AsyncSession, last_run: datetime) -> None:
    """Update thumbnails of projects."""

    # Process all projects requiring a thumbnail update
    projects = await fetch_projects_to_update(async_session, last_run)
    if len(projects) > 0:
        for project in projects:
            try:
                project = project[0]
                user_project = await crud_user_project.get_by_multi_keys(
                    async_session,
                    keys={"user_id": project.user_id, "project_id": project.id},
                )
                layers_project = await crud_layer_project.get_layers(
                    async_session=async_session, project_id=project.id
                )
                if user_project != [] and layers_project != []:
                    print(f"Updating thumbnail for project: {project.id}")

                    old_thumbnail_url = project.thumbnail_url

                    # Create thumbnail
                    print_map = PrintMap(async_session)
                    thumbnail_url = await print_map.create_project_thumbnail(
                        project=project,
                        initial_view_state=user_project[0].initial_view_state,
                        layers_project=layers_project,
                        file_name=str(project.id)
                        + project.updated_at.strftime("_%Y-%m-%d_%H-%M-%S-%f")
                        + ".png",
                    )

                    # Update project with thumbnail url bypassing the model to avoid the table getting a new updated at
                    await async_session.execute(
                        text(
                            """UPDATE customer.project
                                SET thumbnail_url = :thumbnail_url WHERE id = :id""",
                        ),
                        {"thumbnail_url": thumbnail_url, "id": project.id},
                    )
                    await async_session.commit()

                    # Delete old thumbnail from s3 if the thumbnail is not the default thumbnail
                    if (
                        old_thumbnail_url
                        and settings.THUMBNAIL_DIR_PROJECT in old_thumbnail_url
                    ):
                        settings.S3_CLIENT.delete_object(
                            Bucket=settings.AWS_S3_ASSETS_BUCKET,
                            Key=old_thumbnail_url.replace(
                                settings.ASSETS_URL + "/", ""
                            ),
                        )
            except Exception as e:
                print(f"Error updating project thumbnail: {e}")


async def process_layers(async_session: AsyncSession, last_run: datetime) -> None:
    """Update thumbnails of layers."""

    # Process all layers requiring a thumbnail update
    layers = await fetch_layers_to_update(async_session, last_run)

    if len(layers) > 0:
        for layer in layers:
            try:
                layer = layer[0]
                if layer.type in (LayerType.feature, LayerType.table, LayerType.raster):
                    # If there is a feature_layer_type and it is street_network then skip the layer
                    if (
                        layer.feature_layer_type
                        and layer.feature_layer_type == FeatureType.street_network
                    ):
                        continue

                    print(f"Updating thumbnail for layer: {layer.id}")

                    old_thumbnail_url = layer.thumbnail_url

                    # Create thumbnail
                    print_map = PrintMap(async_session)
                    thumbnail_url = await print_map.create_layer_thumbnail(
                        layer=layer,
                        file_name=str(layer.id) + "_" + str(uuid4()) + ".png",
                    )

                    # Update layer with thumbnail url bypassing the model to avoid the table getting a new updated at
                    await async_session.execute(
                        text(
                            """UPDATE customer.layer
                                SET thumbnail_url = :thumbnail_url WHERE id = :id""",
                        ),
                        {"thumbnail_url": thumbnail_url, "id": layer.id},
                    )
                    await async_session.commit()

                    # Delete old thumbnail from s3 if the thumbnail is not the default thumbnail
                    if (
                        old_thumbnail_url
                        and settings.THUMBNAIL_DIR_LAYER in old_thumbnail_url
                    ):
                        settings.S3_CLIENT.delete_object(
                            Bucket=settings.AWS_S3_ASSETS_BUCKET,
                            Key=old_thumbnail_url.replace(
                                settings.ASSETS_URL + "/", ""
                            ),
                        )
            except Exception as e:
                print(f"Error updating layer thumbnail: {e}")


async def main() -> None:
    session_manager.init(settings.ASYNC_SQLALCHEMY_DATABASE_URI)
    async with session_manager.session() as async_session:
        # Get timestamp of last thumbnail update script run
        system_task, last_run = await fetch_last_run_timestamp(
            async_session, SYSTEM_TASK_ID
        )
        current_run = datetime.now(timezone.utc)

        # Update project thumbnails
        await process_projects(async_session, last_run)
        # Update layer thumbnails
        await process_layers(async_session, last_run)

        # Set last run timestamp to current time
        await update_last_run_timestamp(async_session, system_task, current_run)
    await session_manager.close()


if __name__ == "__main__":
    asyncio.run(main())
