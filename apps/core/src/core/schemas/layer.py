# Standard library imports
from enum import Enum
from typing import Annotated, Any, Dict, List, Literal, Optional, Union
from uuid import UUID, uuid4

# Third party imports
from pydantic import (
    BaseModel,
    Field,
    HttpUrl,
    RootModel,
    ValidationError,
    ValidationInfo,
    field_validator,
)
from pyproj import CRS
from pyproj.exceptions import CRSError
from shapely import wkt

# Local application imports
from core.db.models._base_class import DateTimeBase, content_base_example
from core.db.models.layer import (
    DataCategory,
    DataLicense,
    FeatureDataType,
    FeatureGeometryType,
    FeatureLayerExportType,
    FeatureType,
    GeospatialAttributes,
    LayerBase,
    LayerType,
    RasterDataType,
    TableLayerExportType,
    layer_base_example,
    validate_geographical_code,
    validate_language_code,
)
from core.schemas.common import CQLQuery
from core.utils import optional


class UserDataGeomType(Enum):
    point = "point"
    line = "line"
    polygon = "polygon"
    no_geometry = "no_geometry"


class ComputeBreakOperation(Enum):
    """Allowed operations on numeric columns."""

    quantile = "quantile"
    standard_deviation = "standard_deviation"
    equal_interval = "equal_interval"
    heads_and_tails = "heads_and_tails"


class AreaStatisticsOperation(Enum):
    """Allowed operations on polygon geometries."""

    sum = "sum"
    min = "min"
    max = "max"


class LayerReadBaseAttributes(BaseModel):
    user_id: UUID = Field(..., description="User ID of the owner")
    shared_with: Dict[str, Any] | None = Field(
        None, description="List of user IDs the layer is shared with"
    )
    owned_by: Dict[str, Any] | None = Field(None, description="User ID of the owner")


class LayerProperties(BaseModel):
    """Base model for layer properties."""

    type: str = Field(..., description="Mapbox style type", max_length=500)
    paint: Dict[str, Any] = Field(
        ..., description="Paint of the mapbox style of the layer"
    )


################################################################################
# External service DTOs
################################################################################


class ExternalServiceOtherProperties(BaseModel):
    """Model for external service properties."""

    url: str | None = Field(
        default=None,
        description="Layer URL",
    )
    layers: List[str] | None = Field(
        default=None,
        description="List of layers to be displayed",
    )
    width: int | None = Field(
        default=None,
        description="Width of the WMS image",
    )
    height: int | None = Field(
        default=None,
        description="Height of the WMS image",
    )
    srs: str | None = Field(
        default=None,
        description="SRS of the WMS image",
        max_length=50,
    )
    legend_urls: List[str] | None = Field(
        default=None,
        description="Layer legend URLs",
    )

    @field_validator("url", mode="before")
    @classmethod
    def convert_url_httpurl_to_str(
        cls: type["ExternalServiceOtherProperties"], value: str | HttpUrl | None
    ) -> str | None:
        if value is None:
            return value
        elif isinstance(value, HttpUrl):
            return str(value)
        assert HttpUrl(value)
        return value

    @field_validator("legend_urls", mode="before")
    @classmethod
    def convert_legend_urls_httpurl_to_str(
        cls: type["ExternalServiceOtherProperties"],
        value: list[str] | list[HttpUrl] | None,
    ) -> list[str] | None:
        if value is None:
            return value

        result = []
        for v in value:
            if isinstance(v, HttpUrl):
                result.append(str(v))
            else:
                assert HttpUrl(v)
                result.append(v)
        return result


class ExternalServiceAttributesBase(BaseModel):
    """Base model for attributes pertaining to an external service."""

    url: str | None = Field(
        default=None,
        description="Layer URL",
    )
    data_type: FeatureDataType | RasterDataType | None = Field(
        default=None,
        description="Content data type",
    )
    other_properties: ExternalServiceOtherProperties | None = Field(
        default=None,
        description="Additional layer properties.",
    )

    @field_validator("url", mode="before")
    @classmethod
    def convert_httpurl_to_str(
        cls: type["ExternalServiceAttributesBase"], value: str | HttpUrl | None
    ) -> str | None:
        if value is None:
            return value
        elif isinstance(value, HttpUrl):
            return str(value)
        assert HttpUrl(value)
        return value


################################################################################
# File Upload DTOs
################################################################################


################################################################################
# Feature Layer DTOs
################################################################################


class FeatureReadBaseAttributes(
    LayerReadBaseAttributes, LayerBase, GeospatialAttributes
):
    """Base model for feature layer reads."""

    feature_layer_geometry_type: "FeatureGeometryType" = Field(
        ..., description="Feature layer geometry type"
    )
    attribute_mapping: Dict[str, Any] | None = Field(
        default=None, description="Attribute mapping of the layer"
    )
    size: int = Field(..., description="Size of the layer in bytes")
    properties: Dict[str, Any] = Field(
        default_factory=dict, description="Layer properties."
    )

    @field_validator("properties", mode="before")
    @classmethod
    def properties_default(
        cls: type["FeatureReadBaseAttributes"], v: Dict[str, Any] | None
    ) -> Dict[str, Any]:
        """Ensure properties is never None."""
        return v if v is not None else {}


class FeatureUpdateBase(LayerBase, GeospatialAttributes):
    """Base model for feature layer updates."""

    properties: Dict[str, Any] | None = Field(None, description="Layer properties.")


feature_layer_update_base_example = {
    "properties": [
        "match",
        ["get", "category"],
        ["forest"],
        "hsl(137, 37%, 30%)",
        ["park"],
        "hsl(135, 100%, 100%)",
        "#000000",
    ],
    "size": 1000,
}


# Feature Layer Standard
class FeatureStandardRead(
    FeatureReadBaseAttributes, DateTimeBase, ExternalServiceAttributesBase
):
    type: Literal["feature"]
    feature_layer_type: Literal["standard"]


class IFeatureStandardLayerRead(FeatureStandardRead):
    id: UUID = Field(..., description="Content ID of the layer")


@optional
class IFeatureStandardUpdate(FeatureUpdateBase):
    pass


# Feature Layer Tool
class FeatureToolAttributesBase(BaseModel):
    """Base model for additional attributes feature layer tool."""

    tool_type: str | None = Field(None, description="Tool type")


class FeatureToolRead(
    FeatureReadBaseAttributes, FeatureToolAttributesBase, DateTimeBase
):
    """Model to read a feature layer tool."""

    type: Literal["feature"]
    feature_layer_type: Literal["tool"]
    charts: Dict[str, Any] | None = Field(None, description="Chart configuration")


class IFeatureToolLayerRead(FeatureToolRead):
    id: UUID = Field(..., description="Content ID of the layer")


@optional
class IFeatureToolUpdate(FeatureUpdateBase):
    """Model to update a feature layer tool."""

    pass


class FeatureStreetNetworkRead(FeatureReadBaseAttributes, DateTimeBase):
    """Model to read a street network feature layer."""

    type: Literal["feature"]
    feature_layer_type: Literal["street_network"]


class IFeatureStreetNetworkLayerRead(FeatureStreetNetworkRead):
    id: UUID = Field(..., description="Content ID of the layer")


class IFeatureStreetNetworkUpdate(IFeatureStandardUpdate):
    """Model to update a street network feature layer."""

    pass


################################################################################
# Raster DTOs
################################################################################


# Raster Style Property Classes
class RasterStyleImageProperties(BaseModel):
    """Properties for simple image raster style."""

    style_type: Literal["image"] = Field("image", description="Style type identifier")
    band: int = Field(1, ge=1, description="Band number to display (1-indexed)")
    opacity: float = Field(1.0, ge=0.0, le=1.0, description="Layer opacity")
    brightness: float = Field(1.0, ge=0.0, le=2.0, description="Brightness adjustment")
    contrast: float = Field(0.0, ge=-1.0, le=1.0, description="Contrast adjustment")
    saturation: float = Field(0.0, ge=-1.0, le=1.0, description="Saturation adjustment")
    gamma: float = Field(1.0, ge=0.1, le=3.0, description="Gamma correction")


class RasterStyleColorRangeProperties(BaseModel):
    """Properties for color range raster style."""

    style_type: Literal["color_range"] = Field(
        "color_range", description="Style type identifier"
    )
    band: int = Field(1, ge=1, description="Band number to colorize (1-indexed)")
    min_value: float = Field(..., description="Minimum value for color range")
    max_value: float = Field(..., description="Maximum value for color range")
    colors: List[str] = Field(
        ..., min_length=2, description="Array of hex color codes for gradient"
    )
    color_map: List[tuple[float, str]] = Field(
        default_factory=list, description="Custom color stops as (value, color) pairs"
    )
    no_data_color: str | None = Field(
        "transparent", description="Color for no-data values"
    )
    interpolate: bool = Field(True, description="Whether to interpolate between colors")


class RasterStyleCategoriesProperties(BaseModel):
    """Properties for categorical raster style."""

    style_type: Literal["categories"] = Field(
        "categories", description="Style type identifier"
    )
    band: int = Field(1, ge=1, description="Band number to categorize (1-indexed)")
    categories: List[Dict[str, Any]] = Field(
        ...,
        min_length=1,
        description="Array of category definitions with value, color, and optional label",
    )
    default_color: str = Field(
        "#cccccc", description="Default color for uncategorized values"
    )
    no_data_color: str | None = Field(
        "transparent", description="Color for no-data values"
    )


class RasterStyleHillshadeProperties(BaseModel):
    """Properties for hillshade raster style."""

    style_type: Literal["hillshade"] = Field(
        "hillshade", description="Style type identifier"
    )
    band: int = Field(1, ge=1, description="Band number for elevation data (1-indexed)")
    azimuth: float = Field(
        315.0, ge=0.0, le=360.0, description="Light source azimuth angle in degrees"
    )
    altitude: float = Field(
        45.0, ge=0.0, le=90.0, description="Light source altitude angle in degrees"
    )
    z_factor: float = Field(1.0, ge=0.01, description="Vertical exaggeration factor")
    opacity: float = Field(1.0, ge=0.0, le=1.0, description="Layer opacity")


class RasterAttributesBase(ExternalServiceAttributesBase):
    """Base model for attributes pertaining to an external service providing a raster."""

    type: LayerType = Field(..., description="Layer type")
    properties: Dict[str, Any] | None = Field(
        {"visibility": True}, description="Layer properties."
    )

    pass


imagery_layer_attributes_example = {
    "url": "https://geodata.nationaalgeoregister.nl/luchtfoto/rgb/wms?request=GetCapabilities&service=WMS",
    "data_type": "wms",
    "properties": {
        "type": "raster",
        "paint": {"raster-opacity": 1},
    },
    "other_properties": {
        "layers": ["Actueel_ortho25"],
        "width": 256,
        "height": 256,
        "srs": "EPSG:3857",
        "legend_urls": [
            "https://geodata.nationaalgeoregister.nl/luchtfoto/rgb/wms?request=GetLegendGraphic&service=WMS&layer=Actueel_ortho25&format=image/png&width=20&height=20",
            "https://geodata.nationaalgeoregister.nl/luchtfoto/rgb/wms?request=GetLegendGraphic&service=WMS&layer=Actueel_ortho25&format=image/png&width=20&height=20",
        ],
    },
}


class IRasterCreate(LayerBase, GeospatialAttributes, RasterAttributesBase):
    """Model to create a raster layer."""

    pass


class RasterRead(
    LayerReadBaseAttributes,
    LayerBase,
    GeospatialAttributes,
    RasterAttributesBase,
    DateTimeBase,
    ExternalServiceAttributesBase,
):
    """Model to read a raster layer."""

    type: Literal[LayerType.raster]


class IRasterLayerRead(RasterRead):
    id: UUID = Field(..., description="Content ID of the layer")


@optional
class IRasterUpdate(LayerBase, GeospatialAttributes):
    """Model to update a raster layer."""

    url: str | None = Field(None, description="Layer URL")
    properties: Dict[str, Any] | None = Field(None, description="Layer properties.")
    other_properties: ExternalServiceOtherProperties | None = Field(
        None, description="Additional layer properties."
    )

    @field_validator("url", mode="before")
    @classmethod
    def convert_httpurl_to_str(
        cls: type["IRasterUpdate"], value: str | HttpUrl | None
    ) -> str | None:
        if value is None:
            return value
        elif isinstance(value, HttpUrl):
            return str(value)
        assert HttpUrl(value)
        return value


imagery_layer_update_base_example = {
    "url": "https://geodata.nationaalgeoregister.nl/luchtfoto/rgb/wms?request=GetCapabilities&service=WMS",
    "properties": {
        "type": "raster",
        "paint": {"raster-opacity": 0.5},
        "layers": ["Actueel_ortho25"],
        "width": 256,
        "height": 256,
        "srs": "EPSG:3857",
        "legend_urls": [
            "https://geodata.nationaalgeoregister.nl/luchtfoto/rgb/wms?request=GetLegendGraphic&service=WMS&layer=Actueel_ortho25&format=image/png&width=20&height=20",
            "https://geodata.nationaalgeoregister.nl/luchtfoto/rgb/wms?request=GetLegendGraphic&service=WMS&layer=Actueel_ortho25&format=image/png&width=20&height=20",
        ],
    },
}

################################################################################
# Table Layer DTOs
################################################################################


class TableRead(
    LayerBase, LayerReadBaseAttributes, DateTimeBase, ExternalServiceAttributesBase
):
    """Model to read a table layer."""

    type: Literal["table"]
    attribute_mapping: Dict[str, Any] | None = Field(
        default=None, description="Attribute mapping of the layer"
    )


class ITableLayerRead(TableRead):
    id: UUID = Field(..., description="Content ID of the layer")


@optional
class ITableUpdate(LayerBase):
    """Model to update a table layer."""

    pass


layer_creator_class = {
    "feature": {
        "standard": IFeatureStandardLayerRead,
        "tool": IFeatureToolLayerRead,
        "street_network": IFeatureStreetNetworkLayerRead,
    },
    "table": ITableLayerRead,
    "raster": IRasterLayerRead,
}


layer_update_class = {
    "feature": {
        "standard": IFeatureStandardUpdate,
        "tool": IFeatureToolUpdate,
        "street_network": IFeatureStreetNetworkUpdate,
    },
    "raster": IRasterUpdate,
    "table": ITableUpdate,
}


# Write function to get the correct class
def get_layer_schema(
    class_mapping: Dict[str, Any],
    layer_type: LayerType,
    feature_layer_type: FeatureType | None = None,
) -> FeatureUpdateBase | IRasterUpdate | ITableUpdate:
    # Check if layer type is valid
    if layer_type in class_mapping:
        # Check if layer is feature
        if feature_layer_type:
            schema_class = class_mapping[layer_type][feature_layer_type]
            if not issubclass(schema_class, FeatureUpdateBase):
                raise ValueError(
                    f"Feature layer type ({feature_layer_type}) is invalid for layer type ({layer_type})"
                )
            return schema_class
        else:
            schema_class = class_mapping[layer_type]
            if not issubclass(schema_class, IRasterUpdate | ITableUpdate):
                raise ValueError(
                    f"Layer type ({layer_type}) is invalid for the provided class mapping"
                )
            return schema_class
    else:
        raise ValueError(f"Layer type ({layer_type}) is invalid")


class FeatureLayer(
    RootModel[
        Annotated[
            Union[
                IFeatureStandardLayerRead,
                IFeatureToolLayerRead,
                IFeatureStreetNetworkLayerRead,
            ],
            Field(discriminator="feature_layer_type"),
        ]
    ]
):
    pass


class ILayerRead(
    RootModel[
        Annotated[
            Union[
                FeatureLayer,
                ITableLayerRead,
                IRasterLayerRead,
            ],
            Field(discriminator="type"),
        ]
    ]
):
    pass


class IUniqueValue(BaseModel):
    """Model for unique values."""

    value: str = Field(..., description="Unique value")
    count: int = Field(..., description="Number of occurrences")

    @field_validator("value", mode="before")
    @classmethod
    def convert_value_to_str(cls: type["IUniqueValue"], value: str | int) -> str:
        if isinstance(value, str):
            return value
        return str(value)


class ILayerExport(CQLQuery):
    """Layer export input schema."""

    id: UUID = Field(..., description="Layer ID")
    file_type: FeatureLayerExportType | TableLayerExportType = Field(
        ..., description="File type"
    )
    file_name: str = Field(
        ..., description="File name of the exported file.", max_length=500
    )
    crs: str | None = Field(
        None, description="CRS of the exported file.", max_length=20
    )

    # Check if crs is valid
    @field_validator("crs")
    @classmethod
    def validate_crs(cls: type["ILayerExport"], value: str | None) -> str | None:
        # Validate the provided CRS
        try:
            CRS(value)
        except CRSError as e:
            raise ValidationError(f"Invalid CRS: {e}")
        return value

    # Check that projection is EPSG:4326 for KML
    @field_validator("crs")
    @classmethod
    def validate_crs_kml(
        cls: type["ILayerExport"], value: str | None, info: ValidationInfo
    ) -> str | None:
        if info.data["file_type"] == FeatureLayerExportType.kml:
            if value != "EPSG:4326":
                raise ValidationError("KML export only supports EPSG:4326 projection.")
        return value


class LayerGetBase(BaseModel):
    folder_id: UUID | None = Field(
        None,
        description="Folder ID to filter by. If not specified, all layers will be returned.",
    )
    type: List[LayerType] | None = Field(
        None,
        description="Layer type to filter by. Can be multiple. If not specified, all layer types will be returned.",
    )
    feature_layer_type: List[FeatureType] | None = Field(
        None,
        description="Feature layer type to filter by. Can be multiple. If not specified, all feature layer types will be returned.",
    )
    search: str | None = Field(
        None,
        description="Searches the 'name' and 'description' column of the layer. It will convert the text into lower case and see if the passed text is part of the name.",
    )
    license: List[DataLicense] | None = Field(
        None,
        description="List of data licenses",
    )
    data_category: List[DataCategory] | None = Field(
        None,
        description="List of data categories",
    )
    geographical_code: List[str] | None = Field(
        None,
        description="List of geographical codes",
    )
    language_code: List[str] | None = Field(None, description="List of language codes")
    distributor_name: List[str] | None = Field(
        None, description="List of distributor names"
    )
    spatial_search: str | None = Field(None, description="Spatial search for the layer")

    @field_validator("language_code", mode="after", check_fields=False)
    @classmethod
    def language_code_valid(cls, value: list[str]) -> list[str]:
        if value:
            for code in value:
                validate_language_code(code)
        return value

    @field_validator("geographical_code", mode="after", check_fields=False)
    @classmethod
    def geographical_code_valid(cls, value: list[str]) -> list[str]:
        if value:
            for code in value:
                validate_geographical_code(code)
        return value

    # Validate the spatial search
    @field_validator("spatial_search")
    @classmethod
    def validate_spatial_search(cls, value: str | None) -> str | None:
        if value:
            try:
                wkt.loads(value)
            except Exception as e:
                raise ValidationError(f"Invalid Geometry: {e}")
        return value


class ILayerGet(LayerGetBase):
    in_catalog: bool | None = Field(
        None,
        description="This field is left optional. If true, only layers that are in the catalog will be returned.",
    )


class ICatalogLayerGet(LayerGetBase):
    in_catalog: Literal[True] = Field(
        True,
        description="This field is always true. Only layers that are in the catalog will be returned.",
    )


class IMetadataAggregate(LayerGetBase):
    in_catalog: Literal[True] = Field(
        True,
        description="This field is always true. Only layers that are in the catalog will be returned.",
    )


class MetadataGroupAttributes(BaseModel):
    value: str = Field(..., description="Name of the metadata group")
    count: int = Field(..., description="Count of the metadata group")


class IMetadataAggregateRead(BaseModel):
    license: List[MetadataGroupAttributes] = Field(..., description="List of licenses")
    data_category: List[MetadataGroupAttributes] = Field(
        ..., description="List of data categories"
    )
    geographical_code: List[MetadataGroupAttributes] = Field(
        ..., description="List of geographical codes"
    )
    language_code: List[MetadataGroupAttributes] = Field(
        ..., description="List of language codes"
    )
    type: List[MetadataGroupAttributes] = Field(..., description="List of layer types")
    distributor_name: List[MetadataGroupAttributes] = Field(
        ..., description="List of distributor names"
    )


request_examples = {
    "get": {
        "ids": [
            "e7dcaae4-1750-49b7-89a5-9510bf2761ad",
            "e7dcaae4-1750-49b7-89a5-9510bf2761ad",
        ],
    },
    "create": {
        "feature": {
            "summary": "Layer Standard",
            "value": {
                "dataset_id": "699b6116-a8fb-457c-9954-7c9efc9f83ee",
                **content_base_example,
                **layer_base_example,
            },
        },
        "raster": {
            "summary": "Raster Layer",
            "value": {
                **content_base_example,
                **layer_base_example,
                **imagery_layer_attributes_example,
                "type": "raster",
                "extent": "MULTIPOLYGON(((0 0, 0 1, 1 1, 1 0, 0 0)), ((2 2, 2 3, 3 3, 3 2, 2 2)))",
            },
        },
        "table": {
            "summary": "Table Layer",
            "value": {
                "dataset_id": "699b6116-a8fb-457c-9954-7c9efc9f83ee",
                **content_base_example,
                **layer_base_example,
            },
        },
    },
    "export": {
        "feature": {
            "summary": "Layer Standard",
            "value": {
                "id": "699b6116-a8fb-457c-9954-7c9efc9f83ee",
                "file_type": "csv",
                "file_name": "test",
            },
        },
        "table": {
            "summary": "Table Layer",
            "value": {
                "id": "699b6116-a8fb-457c-9954-7c9efc9f83ee",
                "file_type": "csv",
                "file_name": "test",
                "crs": "EPSG:3857",
                "query": {"op": "=", "args": [{"property": "category"}, "bus_stop"]},
            },
        },
    },
    "update": {
        "table": {
            "summary": "Table Layer",
            "value": {
                **content_base_example,
                **layer_base_example,
            },
        },
    },
}
