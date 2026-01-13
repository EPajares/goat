"""FastAPI dependencies for GeoAPI."""

import logging
from typing import Annotated, Optional

from fastapi import Depends, HTTPException, Path, Query
from goatlib.utils.layer import (
    InvalidLayerIdError,
    LayerNotFoundError,
    layer_id_to_table_name,
)
from goatlib.utils.layer import (
    get_schema_for_layer as _goatlib_get_schema_for_layer,
)
from goatlib.utils.layer import (
    normalize_layer_id as _goatlib_normalize_layer_id,
)
from pydantic import BaseModel

from geoapi.ducklake import ducklake_manager

logger = logging.getLogger(__name__)


class LayerInfo(BaseModel):
    """Layer information extracted from URL."""

    layer_id: str
    schema_name: str
    table_name: str

    @property
    def full_table_name(self) -> str:
        """Get full qualified table name."""
        return f"lake.{self.schema_name}.{self.table_name}"


def normalize_layer_id(layer_id: str) -> str:
    """Normalize layer ID to standard UUID format with hyphens.

    Accepts:
    - 32-char hex: abc123def456...
    - UUID format: abc123de-f456-...

    Returns:
        Standard UUID format (lowercase, with hyphens)

    Raises:
        HTTPException: If layer ID is invalid
    """
    try:
        return _goatlib_normalize_layer_id(layer_id)
    except InvalidLayerIdError as e:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid collection ID: {e.layer_id}. Expected UUID format.",
        )


# Alias for backward compatibility
_layer_id_to_table_name = layer_id_to_table_name


def get_schema_for_layer(layer_id: str) -> str:
    """Get schema name for a layer ID, with caching.

    Queries DuckDB's information_schema for the attached DuckLake catalog.

    Args:
        layer_id: Normalized layer ID (UUID format with hyphens)

    Returns:
        Schema name (e.g., 'user_abc123...')

    Raises:
        HTTPException: If layer not found
    """
    try:
        return _goatlib_get_schema_for_layer(layer_id, ducklake_manager)
    except LayerNotFoundError:
        raise HTTPException(
            status_code=404,
            detail=f"Collection not found: {layer_id}",
        )


def get_layer_info(
    collection_id: Annotated[str, Path(alias="collectionId")],
) -> LayerInfo:
    """Extract layer info from collection ID in URL path.

    The collection ID is just the layer UUID (with or without hyphens).
    Schema is looked up from DuckLake catalog with caching.
    """
    layer_id = normalize_layer_id(collection_id)
    schema_name = get_schema_for_layer(layer_id)

    return LayerInfo(
        layer_id=layer_id,
        schema_name=schema_name,
        table_name=_layer_id_to_table_name(layer_id),
    )


# Common query parameters
async def limit_query(
    limit: Annotated[
        int, Query(description="Maximum number of features to return", ge=1, le=100000)
    ] = 10,
) -> int:
    """Limit dependency."""
    return limit


async def offset_query(
    offset: Annotated[int, Query(description="Number of features to skip", ge=0)] = 0,
) -> int:
    """Offset dependency."""
    return offset


async def bbox_query(
    bbox: Annotated[
        Optional[str],
        Query(
            description="Bounding box filter: minx,miny,maxx,maxy",
        ),
    ] = None,
) -> Optional[list[float]]:
    """Parse bbox query parameter."""
    if bbox is None:
        return None

    try:
        coords = [float(c) for c in bbox.split(",")]
        if len(coords) != 4:
            raise ValueError("BBox must have exactly 4 values")
        return coords
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid bbox: {e}")


async def properties_query(
    properties: Annotated[
        Optional[str],
        Query(description="Comma-separated list of properties to return"),
    ] = None,
) -> Optional[list[str]]:
    """Parse properties query parameter."""
    if properties is None or properties == "":
        return None
    return [p.strip() for p in properties.split(",")]


async def cql_filter_query(
    filter: Annotated[
        Optional[str],
        Query(alias="filter", description="CQL2 filter expression"),
    ] = None,
    filter_lang: Annotated[
        Optional[str],
        Query(
            alias="filter-lang", description="Filter language: cql2-json or cql2-text"
        ),
    ] = None,
) -> Optional[dict]:
    """Parse CQL2 filter query parameter.

    Returns a dict with 'filter' (raw string) and 'lang' (cql2-json or cql2-text).
    """
    if filter is None:
        return None

    lang = filter_lang or "cql2-json"  # Default to cql2-json
    if lang not in ("cql2-json", "cql2-text"):
        raise HTTPException(status_code=400, detail=f"Invalid filter-lang: {lang}")

    return {"filter": filter, "lang": lang}


async def tile_params(
    z: Annotated[int, Path(description="Zoom level", ge=0, le=24)],
    x: Annotated[int, Path(description="Tile column")],
    y: Annotated[int, Path(description="Tile row")],
) -> tuple[int, int, int]:
    """Tile coordinate parameters."""
    return z, x, y


async def tile_matrix_set_id(
    tileMatrixSetId: Annotated[str, Path(description="TileMatrixSet identifier")],
) -> str:
    """TileMatrixSet ID parameter."""
    supported = ["WebMercatorQuad", "WorldCRS84Quad"]
    if tileMatrixSetId not in supported:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported TileMatrixSet: {tileMatrixSetId}. "
            f"Supported: {', '.join(supported)}",
        )
    return tileMatrixSetId


# Type aliases for cleaner dependency injection
LayerInfoDep = Annotated[LayerInfo, Depends(get_layer_info)]
LimitDep = Annotated[int, Depends(limit_query)]
OffsetDep = Annotated[int, Depends(offset_query)]
BBoxDep = Annotated[Optional[list[float]], Depends(bbox_query)]
PropertiesDep = Annotated[Optional[list[str]], Depends(properties_query)]
CqlFilterDep = Annotated[Optional[dict], Depends(cql_filter_query)]
TileParamsDep = Annotated[tuple[int, int, int], Depends(tile_params)]
TileMatrixSetIdDep = Annotated[str, Depends(tile_matrix_set_id)]
