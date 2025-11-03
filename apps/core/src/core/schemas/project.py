from datetime import datetime
from enum import Enum
from typing import Any, List, Optional
from uuid import UUID

from pydantic import BaseModel, HttpUrl, ValidationInfo, computed_field, field_validator
from sqlmodel import ARRAY, Column, Field, ForeignKey, SQLModel, Text
from sqlmodel import UUID as UUID_PG

from core.core.config import settings
from core.db.models._base_class import ContentBaseAttributes, DateTimeBase
from core.db.models.layer import internal_layer_table_name
from core.schemas.common import CQLQuery
from core.schemas.layer import (
    ExternalServiceOtherProperties,
    FeatureStandardRead,
    FeatureStreetNetworkRead,
    FeatureToolRead,
    RasterRead,
    TableRead,
)
from core.utils import build_where, optional


################################################################################
# Project DTOs
################################################################################
class ProjectContentType(str, Enum):
    layer = "layer"


class InitialViewState(BaseModel):
    latitude: float = Field(..., description="Latitude", ge=-90, le=90)
    longitude: float = Field(..., description="Longitude", ge=-180, le=180)
    zoom: int = Field(..., description="Zoom level", ge=0, le=20)
    min_zoom: int = Field(..., description="Minimum zoom level", ge=0, le=20)
    max_zoom: int = Field(..., description="Maximum zoom level", ge=0, le=20)
    bearing: int = Field(..., description="Bearing", ge=0, le=360)
    pitch: int = Field(..., description="Pitch", ge=0, le=60)

    @field_validator("zoom", mode="before")
    @classmethod
    def convert_zoom(cls: type["InitialViewState"], value: int | float) -> int:
        if isinstance(value, float):
            return int(value)
        return value

    @field_validator("max_zoom", mode="after")
    @classmethod
    def check_max_zoom(
        cls: type["InitialViewState"], value: int, info: ValidationInfo
    ) -> int:
        min_zoom = info.data.get("min_zoom")
        if min_zoom is not None and value < min_zoom:
            raise ValueError("max_zoom should be greater than or equal to min_zoom")
        return value

    @field_validator("min_zoom", mode="after")
    @classmethod
    def check_min_zoom(
        cls: type["InitialViewState"], value: int, info: ValidationInfo
    ) -> int:
        max_zoom = info.data.get("max_zoom")
        if max_zoom is not None and value > max_zoom:
            raise ValueError("min_zoom should be less than or equal to max_zoom")
        return value


initial_view_state_example = {
    "latitude": 48.1502132,
    "longitude": 11.5696284,
    "zoom": 12,
    "min_zoom": 0,
    "max_zoom": 20,
    "bearing": 0,
    "pitch": 0,
}


class IProjectCreate(ContentBaseAttributes):
    initial_view_state: InitialViewState = Field(
        ..., description="Initial view state of the project"
    )
    tags: List[str] | None = Field(
        default=None,
        sa_column=Column(ARRAY(Text), nullable=True),
        description="Layer tags",
    )


class IProjectRead(ContentBaseAttributes, DateTimeBase):
    id: UUID = Field(..., description="Project ID")
    layer_order: list[int] | None = Field(None, description="Layer order in project")
    thumbnail_url: HttpUrl | None = Field(description="Project thumbnail URL")
    active_scenario_id: UUID | None = Field(None, description="Active scenario ID")
    basemap: str | None = Field(None, description="Project basemap")
    shared_with: dict[str, Any] | None = Field(None, description="Shared with")
    owned_by: dict[str, Any] | None = Field(None, description="Owned by")
    builder_config: dict[str, Any] | None = Field(None, description="Builder config")
    max_extent: list[float] | None = Field(
        None, description="Max extent of the project"
    )
    tags: List[str] | None = Field(
        default=None,
        sa_column=Column(ARRAY(Text), nullable=True),
        description="Layer tags",
    )


class IProjectBaseUpdate(SQLModel):
    folder_id: UUID | None = Field(
        default=None,
        sa_column=Column(
            UUID_PG(as_uuid=True),
            ForeignKey(f"{settings.CUSTOMER_SCHEMA}.folder.id", ondelete="CASCADE"),
            nullable=False,
        ),
        description="Layer folder ID",
    )
    name: str | None = Field(
        default=None,
        sa_type=Text,
        description="Layer name",
        max_length=255,
        nullable=False,
    )
    description: str | None = Field(
        default=None,
        sa_type=Text,
        description="Layer description",
        max_length=2000,
    )
    layer_order: list[int] | None = Field(None, description="Layer order in project")
    basemap: str | None = Field(None, description="Project basemap")
    max_extent: list[float] | None = Field(
        None, description="Max extent of the project"
    )
    active_scenario_id: UUID | None = Field(None, description="Active scenario ID")
    builder_config: dict[str, Any] | None = Field(None, description="Builder config")
    tags: List[str] | None = Field(
        default=None,
        sa_column=Column(ARRAY(Text), nullable=True),
        description="Layer tags",
    )


# TODO: Figure out where this is used, refactor
# class dict(dict):
#     layout: dict = Field(
#         {"visibility": "visible"},
#         description="Layout properties",
#     )
#     minzoom: int = Field(2, description="Minimum zoom level", ge=0, le=22)
#     maxzoom: int = Field(20, description="Maximum zoom level", ge=0, le=22)


class LayerProjectIds(BaseModel):
    id: int = Field(..., description="Layer Project ID")
    layer_id: UUID = Field(..., description="Layer ID")


class IFeatureBaseProject(CQLQuery):
    group: str | None = Field(None, description="Layer group name")
    charts: dict[str, Any] | None = Field(None, description="Layer chart properties")


class IFeatureBaseProjectRead(IFeatureBaseProject):
    properties: dict[str, Any] = Field(
        ...,
        description="Layer properties",
    )
    total_count: int | None = Field(
        None, description="Total count of features in the layer"
    )
    filtered_count: int | None = Field(
        None, description="Filtered count of features in the layer"
    )


class IFeatureStandardProjectRead(
    LayerProjectIds, FeatureStandardRead, IFeatureBaseProjectRead
):
    @computed_field
    def table_name(self) -> str:
        return internal_layer_table_name(self)

    @computed_field
    def where_query(self) -> str | None:
        return where_query(self)


class IFeatureToolProjectRead(
    LayerProjectIds, FeatureToolRead, IFeatureBaseProjectRead
):
    @computed_field
    def table_name(self) -> str:
        return internal_layer_table_name(self)

    @computed_field
    def where_query(self) -> str | None:
        return where_query(self)


class IFeatureStreetNetworkProjectRead(
    LayerProjectIds, FeatureStreetNetworkRead, IFeatureBaseProjectRead
):
    @computed_field
    def table_name(self) -> str:
        return internal_layer_table_name(self)

    @computed_field
    def where_query(self) -> str | None:
        return where_query(self)


class IFeatureStandardProjectUpdate(IFeatureBaseProject):
    name: str | None = Field(None, description="Layer name")
    properties: dict[str, Any] | None = Field(
        default=None,
        description="Layer properties",
    )


class IFeatureStreetNetworkProjectUpdate(IFeatureBaseProject):
    name: str | None = Field(None, description="Layer name")
    properties: dict[str, Any] | None = Field(
        default=None,
        description="Layer properties",
    )


class IFeatureToolProjectUpdate(IFeatureBaseProject):
    name: str | None = Field(None, description="Layer name")
    properties: dict[str, Any] | None = Field(
        default=None,
        description="Layer properties",
    )


class ITableProjectRead(LayerProjectIds, TableRead, CQLQuery):
    group: str | None = Field(None, description="Layer group name", max_length=255)
    total_count: int | None = Field(
        None, description="Total count of features in the layer"
    )
    filtered_count: int | None = Field(
        None, description="Filtered count of features in the layer"
    )

    # Compute table_name and where_query
    @computed_field
    def table_name(self) -> str:
        return internal_layer_table_name(self)

    @computed_field
    def where_query(self) -> str | None:
        return where_query(self)


@optional
class ITableProjectUpdate(CQLQuery):
    name: str | None = Field(None, description="Layer name", max_length=255)
    group: str | None = Field(None, description="Layer group name", max_length=255)


class IRasterProjectRead(LayerProjectIds, RasterRead):
    group: str | None = Field(None, description="Layer group name", max_length=255)
    properties: Optional[dict[str, Any]] = Field(
        None,
        description="Layer properties",
    )


@optional
class IRasterProjectUpdate(BaseModel):
    name: str | None = Field(None, description="Layer name", max_length=255)
    group: str | None = Field(None, description="Layer group name", max_length=255)
    properties: dict[str, Any] | None = Field(
        None,
        description="Layer properties",
    )
    other_properties: ExternalServiceOtherProperties | None = Field(
        None,
        description="Other properties of the layer",
    )


layer_type_mapping_read = {
    "feature_standard": IFeatureStandardProjectRead,
    "feature_tool": IFeatureToolProjectRead,
    "feature_street_network": IFeatureStreetNetworkProjectRead,
    "raster": IRasterProjectRead,
    "table": ITableProjectRead,
}

layer_type_mapping_update = {
    "feature_standard": IFeatureStandardProjectUpdate,
    "feature_tool": IFeatureToolProjectUpdate,
    "feature_street_network": IFeatureStreetNetworkProjectUpdate,
    "raster": IRasterProjectUpdate,
    "table": ITableProjectUpdate,
}


class ProjectPublicProjectConfig(BaseModel):
    id: UUID = Field(..., description="Project ID")
    name: str = Field(..., description="Project name")
    description: str | None = Field(..., description="Project description")
    tags: List[str] | None = Field(default=None, description="Project tags")
    thumbnail_url: HttpUrl | None = Field(None, description="Project thumbnail URL")
    initial_view_state: InitialViewState = Field(
        ..., description="Initial view state of the project"
    )
    basemap: str | None = Field(None, description="Project basemap")
    layer_order: list[int] | None = Field(None, description="Layer order in project")
    max_extent: list[float] | None = Field(
        None, description="Max extent of the project"
    )
    folder_id: UUID = Field(..., description="Folder ID")
    builder_config: dict[str, Any] | None = Field(None, description="Builder config")


class ProjectPublicConfig(BaseModel):
    layers: list[
        IFeatureStreetNetworkProjectRead
        | IFeatureStandardProjectRead
        | IFeatureToolProjectRead
        | ITableProjectRead
        | IRasterProjectRead
    ] = Field(..., description="Layers of the project")
    project: ProjectPublicProjectConfig = Field(
        ..., description="Project configuration"
    )


class ProjectPublicRead(BaseModel):
    created_at: datetime = Field(..., description="Created at")
    updated_at: datetime = Field(..., description="Updated at")
    project_id: UUID
    config: ProjectPublicConfig


def where_query(
    values: IFeatureStandardProjectRead
    | IFeatureToolProjectRead
    | IFeatureStreetNetworkProjectRead
    | ITableProjectRead,
) -> str | None:
    table_name = internal_layer_table_name(values)
    # Check if query exists then build where query
    return build_where(
        id=values.layer_id,
        table_name=table_name,
        query=values.query,
        attribute_mapping=values.attribute_mapping,
    )


# TODO: Refactor
request_examples = {
    "get": {
        "ids": [
            "39e16c27-2b03-498e-8ccc-68e798c64b8d",
            "e7dcaae4-1750-49b7-89a5-9510bf2761ad",
        ],
    },
    "create": {
        "folder_id": "39e16c27-2b03-498e-8ccc-68e798c64b8d",
        "name": "Project 1",
        "description": "Project 1 description",
        "tags": ["tag1", "tag2"],
        "initial_view_state": initial_view_state_example,
    },
    "update": {
        "folder_id": "39e16c27-2b03-498e-8ccc-68e798c64b8d",
        "name": "Project 2",
        "description": "Project 2 description",
        "tags": ["tag1", "tag2"],
    },
    "initial_view_state": initial_view_state_example,
    "update_layer": {
        "feature_standard": {
            "summary": "Feature Layer Standard",
            "value": {
                "name": "Feature Layer Standard",
                "group": "Group 1",
                "query": {"op": "=", "args": [{"property": "category"}, "bus_stop"]},
                "properties": {
                    "type": "circle",
                    "paint": {
                        "circle-radius": 5,
                        "circle-color": "#ff0000",
                    },
                    "layout": {"visibility": "visible"},
                    "minzoom": 0,
                    "maxzoom": 22,
                },
            },
        },
        "feature_tool": {
            "summary": "Feature Layer Tool",
            "value": {
                "name": "Feature Layer Tool",
                "group": "Group 1",
                "properties": {
                    "type": "circle",
                    "paint": {
                        "circle-radius": 5,
                        "circle-color": "#ff0000",
                    },
                    "layout": {"visibility": "visible"},
                    "minzoom": 0,
                    "maxzoom": 22,
                },
            },
        },
        "table": {
            "summary": "Table Layer",
            "value": {
                "name": "Table Layer",
                "group": "Group 1",
            },
        },
        "external_vector": {
            "summary": "VectorVectorTile Layer",
            "value": {
                "name": "VectorVectorTile Layer",
                "group": "Group 1",
            },
        },
        "external_imagery": {
            "summary": "Imagery Layer",
            "value": {
                "name": "Imagery Layer",
                "group": "Group 1",
            },
        },
    },
}
