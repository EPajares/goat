"""Tiles router for OGC Tiles API endpoints."""

import asyncio
import logging

from fastapi import APIRouter, HTTPException, Path, Query, Request, Response

from geoapi.dependencies import (
    BBoxDep,
    CqlFilterDep,
    LayerInfoDep,
    PropertiesDep,
    TileMatrixSetIdDep,
)
from geoapi.models import (
    Link,
    StyleJSON,
    TileJSON,
    TileMatrixSetItem,
    TileMatrixSetsResponse,
    TileSet,
)
from geoapi.services.layer_service import layer_service
from geoapi.services.tile_service import tile_service

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Tiles"])


@router.get(
    "/collections/{collectionId}/tiles/{tileMatrixSetId}/{z}/{x}/{y}",
    summary="Get vector tile",
    response_class=Response,
    responses={
        200: {
            "content": {"application/vnd.mapbox-vector-tile": {}},
            "description": "Mapbox Vector Tile",
        },
        204: {"description": "Empty tile"},
        404: {"description": "Collection not found"},
    },
)
async def get_tile(
    request: Request,
    layer_info: LayerInfoDep,
    tileMatrixSetId: TileMatrixSetIdDep,
    z: int = Path(..., ge=0, le=24, description="Zoom level"),
    x: int = Path(..., ge=0, description="Tile column"),
    y: int = Path(..., ge=0, description="Tile row"),
    properties: PropertiesDep = None,
    cql_filter: CqlFilterDep = None,
    bbox: BBoxDep = None,
    limit: int = Query(default=None, ge=1, le=100000, description="Max features"),
) -> Response:
    """Get a vector tile for the specified collection and tile coordinates."""
    # Get layer metadata for column validation
    metadata = await layer_service.get_layer_metadata(layer_info)

    if not metadata:
        raise HTTPException(status_code=404, detail="Collection not found")

    if not metadata.has_geometry:
        raise HTTPException(status_code=400, detail="Collection has no geometry column")

    columns = metadata.columns
    geometry_column = metadata.geometry_column

    # Run synchronous DuckDB tile generation in thread pool to avoid blocking event loop
    tile_data = await asyncio.to_thread(
        tile_service.get_tile,
        layer_info=layer_info,
        z=z,
        x=x,
        y=y,
        properties=properties,
        cql_filter=cql_filter,
        bbox=bbox,
        limit=limit,
        columns=columns,
        geometry_column=geometry_column,
    )

    if not tile_data:
        return Response(status_code=204)

    return Response(
        content=tile_data,
        media_type="application/vnd.mapbox-vector-tile",
        headers={
            "Cache-Control": "public, max-age=3600",
        },
    )


@router.get(
    "/collections/{collectionId}/tiles",
    summary="List available tilesets",
    response_model=list[TileSet],
)
async def list_tilesets(
    request: Request,
    layer_info: LayerInfoDep,
) -> list[TileSet]:
    """List available tile matrix sets for a collection."""
    base_url = str(request.base_url).rstrip("/")
    collection_id = layer_info.layer_id

    tilesets = []
    for tms_id in ["WebMercatorQuad", "WorldCRS84Quad"]:
        tilesets.append(
            TileSet(
                title=f"{collection_id} - {tms_id}",
                tileMatrixSetURI=f"http://www.opengis.net/def/tilematrixset/OGC/1.0/{tms_id}",
                dataType="vector",
                links=[
                    Link(
                        href=f"{base_url}/collections/{collection_id}/tiles/{tms_id}",
                        rel="self",
                        type="application/json",
                    ),
                    Link(
                        href=f"{base_url}/collections/{collection_id}/tiles/{tms_id}/{{z}}/{{x}}/{{y}}",
                        rel="item",
                        type="application/vnd.mapbox-vector-tile",
                        templated=True,
                    ),
                ],
            )
        )
    return tilesets


@router.get(
    "/collections/{collectionId}/tiles/{tileMatrixSetId}",
    summary="Get tileset metadata",
    response_model=TileSet,
)
async def get_tileset(
    request: Request,
    layer_info: LayerInfoDep,
    tileMatrixSetId: TileMatrixSetIdDep,
) -> TileSet:
    """Get tileset metadata for a collection."""
    base_url = str(request.base_url).rstrip("/")
    collection_id = layer_info.layer_id

    return TileSet(
        title=f"{collection_id} - {tileMatrixSetId}",
        tileMatrixSetURI=f"http://www.opengis.net/def/tilematrixset/OGC/1.0/{tileMatrixSetId}",
        dataType="vector",
        links=[
            Link(
                href=f"{base_url}/collections/{collection_id}/tiles/{tileMatrixSetId}",
                rel="self",
                type="application/json",
            ),
            Link(
                href=f"{base_url}/collections/{collection_id}/tiles/{tileMatrixSetId}/{{z}}/{{x}}/{{y}}",
                rel="item",
                type="application/vnd.mapbox-vector-tile",
                templated=True,
            ),
            Link(
                href=f"{base_url}/collections/{collection_id}/tiles/{tileMatrixSetId}/tilejson.json",
                rel="describedby",
                type="application/json",
                title="TileJSON",
            ),
        ],
    )


@router.get(
    "/collections/{collectionId}/tiles/{tileMatrixSetId}/tilejson.json",
    summary="Get TileJSON",
    response_model=TileJSON,
)
async def get_tilejson(
    request: Request,
    layer_info: LayerInfoDep,
    tileMatrixSetId: TileMatrixSetIdDep,
    minzoom: int = Query(default=0, ge=0, le=24),
    maxzoom: int = Query(default=22, ge=0, le=24),
) -> TileJSON:
    """Get TileJSON document for a collection."""
    metadata = await layer_service.get_layer_metadata(layer_info)
    if not metadata:
        raise HTTPException(status_code=404, detail="Collection not found")

    base_url = str(request.base_url).rstrip("/")
    collection_id = layer_info.layer_id

    # Build vector layer fields
    fields = {}
    for col in metadata.columns:
        if col["name"] not in ("geom", "geometry"):
            fields[col["name"]] = col["json_type"]

    vector_layers = [
        {
            "id": "default",
            "fields": fields,
            "minzoom": minzoom,
            "maxzoom": maxzoom,
        }
    ]

    # Build tile URL with query params
    tile_url = f"{base_url}/collections/{collection_id}/tiles/{tileMatrixSetId}/{{z}}/{{x}}/{{y}}"

    # Forward query parameters to tile URL
    query_params = []
    for key, value in request.query_params.items():
        if key not in ("minzoom", "maxzoom"):
            query_params.append(f"{key}={value}")
    if query_params:
        tile_url += "?" + "&".join(query_params)

    return TileJSON(
        name=metadata.name,
        tiles=[tile_url],
        vector_layers=vector_layers,
        minzoom=minzoom,
        maxzoom=maxzoom,
        bounds=metadata.bounds,
        center=[
            (metadata.bounds[0] + metadata.bounds[2]) / 2,
            (metadata.bounds[1] + metadata.bounds[3]) / 2,
            0,
        ],
    )


@router.get(
    "/collections/{collectionId}/tiles/{tileMatrixSetId}/style.json",
    summary="Get StyleJSON",
    response_model=StyleJSON,
)
async def get_stylejson(
    request: Request,
    layer_info: LayerInfoDep,
    tileMatrixSetId: TileMatrixSetIdDep,
    minzoom: int = Query(default=0, ge=0, le=24),
    maxzoom: int = Query(default=22, ge=0, le=24),
) -> StyleJSON:
    """Get MapLibre StyleJSON document for a collection."""
    metadata = await layer_service.get_layer_metadata(layer_info)
    if not metadata:
        raise HTTPException(status_code=404, detail="Collection not found")

    base_url = str(request.base_url).rstrip("/")
    collection_id = layer_info.layer_id

    tile_url = f"{base_url}/collections/{collection_id}/tiles/{tileMatrixSetId}/{{z}}/{{x}}/{{y}}"

    # Create style layers based on geometry type
    layers = []
    geom_type = (metadata.geometry_type or "polygon").lower()

    if geom_type in ("polygon", "multipolygon"):
        layers.append(
            {
                "id": f"{collection_id}_fill",
                "source": collection_id,
                "source-layer": "default",
                "type": "fill",
                "paint": {
                    "fill-color": "rgba(200, 100, 240, 0.4)",
                    "fill-outline-color": "#000",
                },
            }
        )
    elif geom_type in ("linestring", "multilinestring", "line"):
        layers.append(
            {
                "id": f"{collection_id}_line",
                "source": collection_id,
                "source-layer": "default",
                "type": "line",
                "paint": {
                    "line-color": "#000",
                    "line-width": 2,
                },
            }
        )
    elif geom_type in ("point", "multipoint"):
        layers.append(
            {
                "id": f"{collection_id}_circle",
                "source": collection_id,
                "source-layer": "default",
                "type": "circle",
                "paint": {
                    "circle-color": "#3388ff",
                    "circle-radius": 5,
                    "circle-stroke-color": "#fff",
                    "circle-stroke-width": 1,
                },
            }
        )
    else:
        # Generic layers for unknown geometry
        layers.extend(
            [
                {
                    "id": f"{collection_id}_fill",
                    "source": collection_id,
                    "source-layer": "default",
                    "type": "fill",
                    "filter": ["==", ["geometry-type"], "Polygon"],
                    "paint": {"fill-color": "rgba(200, 100, 240, 0.4)"},
                },
                {
                    "id": f"{collection_id}_line",
                    "source": collection_id,
                    "source-layer": "default",
                    "type": "line",
                    "filter": ["==", ["geometry-type"], "LineString"],
                    "paint": {"line-color": "#000", "line-width": 2},
                },
                {
                    "id": f"{collection_id}_circle",
                    "source": collection_id,
                    "source-layer": "default",
                    "type": "circle",
                    "filter": ["==", ["geometry-type"], "Point"],
                    "paint": {"circle-color": "#3388ff", "circle-radius": 5},
                },
            ]
        )

    return StyleJSON(
        name=metadata.name,
        sources={
            collection_id: {
                "type": "vector",
                "tiles": [tile_url],
                "minzoom": minzoom,
                "maxzoom": maxzoom,
                "bounds": metadata.bounds,
            }
        },
        layers=layers,
        center=[
            (metadata.bounds[0] + metadata.bounds[2]) / 2,
            (metadata.bounds[1] + metadata.bounds[3]) / 2,
        ],
        zoom=0,
    )


@router.get(
    "/tileMatrixSets",
    summary="List tile matrix sets",
    response_model=TileMatrixSetsResponse,
)
async def list_tile_matrix_sets(request: Request) -> TileMatrixSetsResponse:
    """List available tile matrix sets."""
    base_url = str(request.base_url).rstrip("/")

    return TileMatrixSetsResponse(
        tileMatrixSets=[
            TileMatrixSetItem(
                id="WebMercatorQuad",
                title="Web Mercator Quad",
                links=[
                    Link(
                        href=f"{base_url}/tileMatrixSets/WebMercatorQuad",
                        rel="self",
                        type="application/json",
                    )
                ],
            ),
            TileMatrixSetItem(
                id="WorldCRS84Quad",
                title="World CRS84 Quad",
                links=[
                    Link(
                        href=f"{base_url}/tileMatrixSets/WorldCRS84Quad",
                        rel="self",
                        type="application/json",
                    )
                ],
            ),
        ]
    )


@router.get(
    "/tileMatrixSets/{tileMatrixSetId}",
    summary="Get tile matrix set",
)
async def get_tile_matrix_set(
    request: Request,
    tileMatrixSetId: TileMatrixSetIdDep,
) -> dict:
    """Get tile matrix set definition."""
    # Return basic TMS info (full OGC TMS definition would be much larger)
    tms_info = {
        "WebMercatorQuad": {
            "id": "WebMercatorQuad",
            "title": "Web Mercator Quad",
            "uri": "http://www.opengis.net/def/tilematrixset/OGC/1.0/WebMercatorQuad",
            "crs": "http://www.opengis.net/def/crs/EPSG/0/3857",
            "wellKnownScaleSet": "http://www.opengis.net/def/wkss/OGC/1.0/GoogleMapsCompatible",
        },
        "WorldCRS84Quad": {
            "id": "WorldCRS84Quad",
            "title": "World CRS84 Quad",
            "uri": "http://www.opengis.net/def/tilematrixset/OGC/1.0/WorldCRS84Quad",
            "crs": "http://www.opengis.net/def/crs/OGC/1.3/CRS84",
            "wellKnownScaleSet": "http://www.opengis.net/def/wkss/OGC/1.0/GoogleCRS84Quad",
        },
    }

    return tms_info.get(tileMatrixSetId, {})
