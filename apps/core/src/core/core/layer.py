# Standard library imports
import re
from enum import Enum
from typing import Any, Dict, Union
from uuid import UUID

# Third party imports
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import select
from sqlmodel import SQLModel

# Local application imports
from core.core.config import settings
from core.crud.base import CRUDBase
from core.db.models._link_model import LayerProjectLink
from core.db.models.layer import (
    FeatureType,
    Layer,
    LayerType,
)


def model_to_dict(model: SQLModel | BaseModel) -> Dict[str, Any]:
    model_dict = model.model_dump()
    for key, value in model_dict.items():
        if isinstance(value, Enum):
            model_dict[key] = value.value
    return model_dict


def get_user_table(layer: Union[dict, SQLModel, BaseModel]) -> str:
    """Get the table with the user data based on the layer metadata."""

    # Check if layer is of type dict or SQLModel/BaseModel
    if isinstance(layer, (SQLModel, BaseModel)):
        layer = model_to_dict(layer)

    if isinstance(layer, dict):
        if layer["type"] == LayerType.feature.value:
            if layer["feature_layer_type"] in (FeatureType.standard, FeatureType.tool):
                table_prefix = layer["feature_layer_geometry_type"]
            elif layer["feature_layer_type"] == FeatureType.street_network:
                table_prefix = (
                    FeatureType.street_network.value
                    + "_"
                    + layer["feature_layer_geometry_type"]
                )
        elif layer["type"] == LayerType.table.value:
            table_prefix = "no_geometry"
        else:
            raise ValueError(f"The passed layer type {layer['type']} is not supported.")
    user_id = layer["user_id"]
    return f"{settings.USER_DATA_SCHEMA}.{table_prefix}_{str(user_id).replace('-', '')}"


class CRUDLayerBase(CRUDBase):
    async def check_and_alter_layer_name(
        self,
        async_session: AsyncSession,
        folder_id: UUID,
        layer_name: str,
        project_id: UUID | None = None,
    ) -> str:
        """Check if layer name already exists in project and alter it like layer (n+1) if necessary"""

        # Regular expression to find layer names with a number
        pattern = re.compile(rf"^{re.escape(layer_name)} \((\d+)\)$")

        # Get all layer names in project
        if project_id:
            names_in_project = await async_session.execute(
                select(LayerProjectLink.name).where(
                    LayerProjectLink.project_id == project_id,
                    LayerProjectLink.name.like(f"{layer_name}%"),
                )
            )
            layer_names = [row[0] for row in names_in_project.fetchall()]
        else:
            layer_names = []

        # Get all layer names in folder
        names_in_folder = [
            row[0]
            for row in (
                await async_session.execute(
                    select(Layer.name).where(
                        Layer.folder_id == folder_id,
                        Layer.name.like(f"{layer_name}%"),
                    )
                )
            ).fetchall()
        ]
        layer_names = list(set(layer_names + names_in_folder))

        # Find the highest number (n) among the layer names using list comprehension
        numbers = [
            int(match.group(1))
            for name in layer_names
            if (match := pattern.match(name))
        ]
        highest_num = max(numbers, default=0)

        # Check if the base layer name exists
        base_name_exists = layer_name in layer_names

        # Construct the new layer name
        if base_name_exists or highest_num > 0:
            new_layer_name = f"{layer_name} ({highest_num + 1})"
        else:
            new_layer_name = layer_name

        return new_layer_name
