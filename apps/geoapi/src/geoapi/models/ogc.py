"""Pydantic models for OGC API responses."""

from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


class GeometryType(str, Enum):
    """Geometry types."""

    point = "Point"
    line = "LineString"
    polygon = "Polygon"
    multipoint = "MultiPoint"
    multiline = "MultiLineString"
    multipolygon = "MultiPolygon"


class Link(BaseModel):
    """OGC API Link."""

    href: str
    rel: str
    type: Optional[str] = None
    title: Optional[str] = None
    templated: Optional[bool] = None


class SpatialExtent(BaseModel):
    """Spatial extent with bounding box."""

    bbox: list[list[float]]
    crs: str = "http://www.opengis.net/def/crs/OGC/1.3/CRS84"


class Extent(BaseModel):
    """Collection extent."""

    spatial: Optional[SpatialExtent] = None


class Collection(BaseModel):
    """OGC API Collection metadata."""

    id: str
    title: Optional[str] = None
    description: Optional[str] = None
    links: list[Link] = Field(default_factory=list)
    extent: Optional[Extent] = None
    itemType: str = "feature"
    crs: list[str] = Field(
        default_factory=lambda: ["http://www.opengis.net/def/crs/OGC/1.3/CRS84"]
    )


class CollectionsResponse(BaseModel):
    """Response for listing collections."""

    links: list[Link] = Field(default_factory=list)
    numberMatched: int
    numberReturned: int
    collections: list[Collection]


class QueryableProperty(BaseModel):
    """A queryable property."""

    name: str
    type: str
    title: Optional[str] = None


class Queryables(BaseModel):
    """Collection queryables."""

    model_config = {"populate_by_name": True}

    title: str
    type: str = "object"
    properties: dict[str, Any]
    schema_: str = Field(
        "https://json-schema.org/draft/2019-09/schema",
        alias="$schema",
        serialization_alias="$schema",
    )
    id_: Optional[str] = Field(None, alias="$id", serialization_alias="$id")


class Feature(BaseModel):
    """GeoJSON Feature."""

    type: str = "Feature"
    id: Optional[Any] = None
    geometry: Optional[dict[str, Any]] = None
    properties: Optional[dict[str, Any]] = None
    links: list[Link] = Field(default_factory=list)


class FeatureCollection(BaseModel):
    """GeoJSON FeatureCollection."""

    type: str = "FeatureCollection"
    features: list[Feature] = Field(default_factory=list)
    links: list[Link] = Field(default_factory=list)
    numberMatched: Optional[int] = None
    numberReturned: Optional[int] = None


class TileMatrixSetItem(BaseModel):
    """TileMatrixSet list item."""

    id: str
    title: Optional[str] = None
    links: list[Link] = Field(default_factory=list)


class TileMatrixSetsResponse(BaseModel):
    """Response for TileMatrixSets list."""

    tileMatrixSets: list[TileMatrixSetItem]


class TileSet(BaseModel):
    """OGC TileSet metadata."""

    title: Optional[str] = None
    tileMatrixSetURI: str
    dataType: str = "vector"
    crs: str = "http://www.opengis.net/def/crs/EPSG/0/3857"
    links: list[Link] = Field(default_factory=list)


class TileJSON(BaseModel):
    """TileJSON 3.0 document."""

    tilejson: str = "3.0.0"
    name: Optional[str] = None
    description: Optional[str] = None
    version: str = "1.0.0"
    attribution: Optional[str] = None
    scheme: str = "xyz"
    tiles: list[str]
    vector_layers: list[dict[str, Any]] = Field(default_factory=list)
    minzoom: int = 0
    maxzoom: int = 22
    bounds: Optional[list[float]] = None
    center: Optional[list[float]] = None


class StyleJSON(BaseModel):
    """MapLibre StyleJSON document."""

    version: int = 8
    name: Optional[str] = None
    sources: dict[str, Any] = Field(default_factory=dict)
    layers: list[dict[str, Any]] = Field(default_factory=list)
    center: Optional[list[float]] = None
    zoom: Optional[float] = None


class Conformance(BaseModel):
    """Conformance classes."""

    conformsTo: list[str]


class LandingPage(BaseModel):
    """Landing page response."""

    title: str
    description: Optional[str] = None
    links: list[Link] = Field(default_factory=list)


class HealthCheck(BaseModel):
    """Health check response."""

    status: str = "ok"
    ping: str = "pong"
