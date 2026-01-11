# Standard library imports
from typing import List, Tuple, Union
from uuid import UUID

# Third party imports
from fastapi import HTTPException, status
from pydantic import BaseModel, TypeAdapter, ValidationError
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from core.core.layer import CRUDLayerBase
from core.core.statistics import StatisticsBase
from core.db.models._link_model import LayerProjectLink
from core.db.models.layer import Layer
from core.db.models.project import Project
from core.schemas.error import LayerNotFoundError, UnsupportedLayerTypeError
from core.schemas.layer import (
    FeatureGeometryType,
    LayerType,
)
from core.schemas.project import (
    IFeatureStandardProjectRead,
    IFeatureStreetNetworkProjectRead,
    IFeatureToolProjectRead,
    IRasterProjectRead,
    ITableProjectRead,
    layer_type_mapping_read,
    layer_type_mapping_update,
)

# Local application imports
from .base import CRUDBase


class CRUDLayerProject(CRUDLayerBase, StatisticsBase):
    async def layer_projects_to_schemas(
        self,
        async_session: AsyncSession,
        layers_project: List[Tuple[Layer, LayerProjectLink]],
    ) -> List[
        IFeatureStandardProjectRead
        | IFeatureToolProjectRead
        | IFeatureStreetNetworkProjectRead
        | ITableProjectRead
        | IRasterProjectRead
    ]:
        """Convert layer projects to schemas."""
        layer_projects_schemas = []

        # Loop through layer and layer projects
        for layer_project_tuple in layers_project:
            layer = layer_project_tuple[0]
            layer_project_model = layer_project_tuple[1]

            # Get layer type
            if layer.feature_layer_type is not None:
                layer_type = layer.type + "_" + layer.feature_layer_type
            else:
                layer_type = layer.type

            layer_dict = layer.model_dump()
            # Delete id from layer
            del layer_dict["id"]
            # Update layer with layer project
            layer_dict.update(layer_project_model.model_dump())
            layer_project: Union[
                IFeatureStandardProjectRead
                | IFeatureToolProjectRead
                | IFeatureStreetNetworkProjectRead
                | ITableProjectRead
                | IRasterProjectRead
            ] = layer_type_mapping_read[layer_type](**layer_dict)

            # Write into correct schema
            # Note: total_count and filtered_count are fetched on-demand via geoapi
            layer_projects_schemas.append(layer_project)

        return layer_projects_schemas

    async def get_layers(
        self,
        async_session: AsyncSession,
        project_id: UUID,
    ) -> List[
        IFeatureStandardProjectRead
        | IFeatureToolProjectRead
        | IFeatureStreetNetworkProjectRead
        | ITableProjectRead
        | IRasterProjectRead
    ]:
        """Get all layers from a project, sorted by layer_order.

        Layers are returned in the order defined by the project's layer_order
        array. Layers at the beginning of layer_order appear first (on top in UI).
        """
        # Get project to retrieve layer_order
        project = await CRUDBase(Project).get(async_session, id=project_id)
        layer_order = project.layer_order or []

        # Get all layers from project
        query = select(Layer, LayerProjectLink).where(
            LayerProjectLink.project_id == project_id,
            Layer.id == LayerProjectLink.layer_id,
        )

        # Get all layers from project
        layer_projects_to_schemas = await self.layer_projects_to_schemas(
            async_session,
            await self.get_multi(
                async_session,
                query=query,
            ),
        )

        # Sort layers by layer_order array (first in array = first in result = on top)
        if layer_order:
            order_map = {
                layer_project_id: idx
                for idx, layer_project_id in enumerate(layer_order)
            }
            layer_projects_to_schemas.sort(
                key=lambda layer: order_map.get(layer.id, len(layer_order))
            )

        return layer_projects_to_schemas

    async def get_by_ids(
        self, async_session: AsyncSession, ids: list[int]
    ) -> List[
        IFeatureStandardProjectRead
        | IFeatureToolProjectRead
        | IFeatureStreetNetworkProjectRead
        | ITableProjectRead
        | IRasterProjectRead
    ]:
        """Get all layer projects links by the ids"""

        # Get all layers from project by id
        query = (
            select(Layer, LayerProjectLink)
            .where(
                LayerProjectLink.id.in_(ids),
            )
            .where(
                Layer.id == LayerProjectLink.layer_id,
            )
        )

        # Get all layers from project
        layer_projects = await self.layer_projects_to_schemas(
            async_session,
            await self.get_multi(
                async_session,
                query=query,
            ),
        )
        return layer_projects

    async def get_internal(
        self,
        async_session: AsyncSession,
        id: int,
        project_id: UUID,
        expected_layer_types: List[Union[LayerType.feature, LayerType.table]] = [
            LayerType.feature
        ],
        expected_geometry_types: List[FeatureGeometryType] | None = None,
    ) -> BaseModel:
        """Get internal layer from layer project"""

        # Get layer project
        query = select(Layer, LayerProjectLink).where(
            LayerProjectLink.id == id,
            Layer.id == LayerProjectLink.layer_id,
            LayerProjectLink.project_id == project_id,
        )
        all_layer_projects = await self.layer_projects_to_schemas(
            async_session,
            await self.get_multi(
                db=async_session,
                query=query,
            ),
        )

        # Make sure layer project exists
        if all_layer_projects == []:
            raise LayerNotFoundError("Layer projects not found")
        layer_project = all_layer_projects[0]
        # Check if one of the expected layer types is given
        if layer_project.type not in expected_layer_types:
            raise UnsupportedLayerTypeError(
                f"Layer {layer_project.name} is not a {[layer_type.value for layer_type in expected_layer_types]} layer"
            )

        # Check if geometry type is correct
        if layer_project.type == LayerType.feature.value:
            if expected_geometry_types is not None:
                if (
                    layer_project.feature_layer_geometry_type
                    not in expected_geometry_types
                ):
                    raise UnsupportedLayerTypeError(
                        f"Layer {layer_project.name} is not a {[geom_type.value for geom_type in expected_geometry_types]} layer"
                    )

        return layer_project

    async def create(
        self,
        async_session: AsyncSession,
        project_id: UUID,
        layer_ids: List[UUID],
    ) -> List[BaseModel]:
        """Create a link between a project and a layer"""

        # Remove duplicate layer_ids
        layer_ids = list(set(layer_ids))

        # Get number of layers in project
        layer_projects = await self.get_multi(
            async_session,
            query=select(LayerProjectLink).where(
                LayerProjectLink.project_id == project_id
            ),
        )

        # Check if maximum number of layers in project is reached. In case layer_project is empty just go on.
        if layer_projects != []:
            if len(layer_projects) + len(layer_ids) >= 300:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Maximum number of layers in project reached",
                )

        layers = await CRUDBase(Layer).get_multi(
            async_session,
            query=select(Layer).where(Layer.id.in_(layer_ids)),
        )

        if len(layers) != len(layer_ids):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="One or several Layers were not found",
            )

        # Define array for layer project ids
        layer_project_ids = []

        # Create link between project and layer
        for layer in layers:
            layer = layer[0]

            # Check if layer with same name and ID already exists in project. Then the layer should be duplicated with a new name.
            layer_name = layer.name
            if layer_projects != []:
                if layer.name in [
                    layer_project[0].name for layer_project in layer_projects
                ]:
                    layer_name = "Copy from " + layer.name

            # Create layer project link
            layer_project = LayerProjectLink(
                project_id=project_id,
                layer_id=layer.id,
                name=layer_name,
                properties=layer.properties,
                other_properties=layer.other_properties,
            )

            # Add to database
            layer_project = await CRUDBase(LayerProjectLink).create(
                async_session,
                obj_in=layer_project.model_dump(),
            )
            layer_project_ids.append(layer_project.id)

        # Get project to update layer order
        project = await CRUDBase(Project).get(async_session, id=project_id)
        layer_order = project.layer_order
        # Add layer ids to the beginning of the list
        if layer_order is None:
            layer_order = layer_project_ids
        else:
            layer_order = layer_project_ids + layer_order

        # Update project layer order
        project = await CRUDBase(Project).update(
            async_session,
            db_obj=project,
            obj_in={"layer_order": layer_order},
        )
        layers = await self.get_by_ids(async_session, ids=layer_project_ids)
        return layers

    async def update(
        self,
        async_session: AsyncSession,
        id: int,
        layer_in: dict,
    ) -> (
        IFeatureStandardProjectRead
        | IFeatureToolProjectRead
        | IFeatureStreetNetworkProjectRead
        | ITableProjectRead
        | IRasterProjectRead
    ):
        """Update a link between a project and a layer"""

        # Get layer project
        layer_project_old = await self.get(
            async_session,
            id=id,
        )
        layer_id = layer_project_old.layer_id

        # Get base layer object
        layer = await CRUDBase(Layer).get(async_session, id=layer_id)
        layer_dict = layer.dict()

        # Get right schema for respective layer type
        if layer.feature_layer_type is not None:
            model_type_update = layer_type_mapping_update.get(
                layer.type + "_" + layer.feature_layer_type
            )
            model_type_read = layer_type_mapping_read.get(
                layer.type + "_" + layer.feature_layer_type
            )
        else:
            model_type_update = layer_type_mapping_update.get(layer.type)
            model_type_read = layer_type_mapping_read.get(layer.type)

        # Parse and validate the data against the model
        try:
            layer_in = TypeAdapter(model_type_update).validate_python(layer_in)
        except ValidationError as e:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=str(e),
            )

        if layer_project_old is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Layer project not found"
            )

        # Update layer project
        layer_project = await CRUDBase(LayerProjectLink).update(
            async_session,
            db_obj=layer_project_old,
            obj_in=layer_in,
        )
        layer_project_dict = layer_project.dict()
        del layer_dict["id"]
        # Update layer
        layer_dict.update(layer_project_dict)
        layer_project = model_type_read(**layer_dict)
        # Note: total_count and filtered_count are fetched on-demand via geoapi
        return layer_project

    async def update_layer_id(
        self,
        async_session: AsyncSession,
        layer_id: UUID,
        new_layer_id: UUID,
    ) -> None:
        """Update layer id in layer project link."""

        # Update all layers from project by id
        query = (
            update(LayerProjectLink)
            .where(LayerProjectLink.layer_id == layer_id)
            .values(layer_id=new_layer_id)
        )

        async with async_session.begin():
            await async_session.execute(query)
            await async_session.commit()


layer_project = CRUDLayerProject(LayerProjectLink)
