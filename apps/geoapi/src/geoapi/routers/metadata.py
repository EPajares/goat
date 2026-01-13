"""Metadata router for OGC API collection and conformance endpoints."""

from fastapi import APIRouter, HTTPException, Request

from geoapi.config import settings
from geoapi.dependencies import LayerInfoDep
from geoapi.models import (
    Collection,
    Conformance,
    Extent,
    LandingPage,
    Link,
    Queryables,
    SpatialExtent,
)
from geoapi.services.layer_service import layer_service

router = APIRouter(tags=["Metadata"])


# OGC conformance classes
CONFORMANCE_CLASSES = [
    # Common
    "http://www.opengis.net/spec/ogcapi-common-1/1.0/conf/core",
    "http://www.opengis.net/spec/ogcapi-common-1/1.0/conf/landingPage",
    "http://www.opengis.net/spec/ogcapi-common-2/1.0/conf/collections",
    "http://www.opengis.net/spec/ogcapi-common-1/1.0/conf/json",
    "http://www.opengis.net/spec/ogcapi-common-1/1.0/conf/oas30",
    # Features
    "http://www.opengis.net/spec/ogcapi-features-1/1.0/conf/core",
    "http://www.opengis.net/spec/ogcapi-features-1/1.0/conf/geojson",
    "http://www.opengis.net/spec/ogcapi-features-1/1.0/conf/oas30",
    "http://www.opengis.net/spec/ogcapi-features-3/1.0/conf/filter",
    "http://www.opengis.net/spec/ogcapi-features-3/1.0/conf/features-filter",
    # Tiles
    "http://www.opengis.net/spec/ogcapi-tiles-1/1.0/conf/core",
    "http://www.opengis.net/spec/ogcapi-tiles-1/1.0/conf/mvt",
    "http://www.opengis.net/spec/ogcapi-tiles-1/1.0/conf/tileset",
    "http://www.opengis.net/spec/ogcapi-tiles-1/1.0/conf/tilesets-list",
]


@router.get(
    "/",
    summary="Landing page",
    response_model=LandingPage,
)
async def landing_page(request: Request) -> LandingPage:
    """OGC API landing page."""
    base_url = str(request.base_url).rstrip("/")

    return LandingPage(
        title=settings.APP_NAME,
        description="OGC Features and Tiles API for GOAT layers",
        links=[
            Link(
                href=base_url,
                rel="self",
                type="application/json",
                title="Landing page",
            ),
            Link(
                href=f"{base_url}/api",
                rel="service-desc",
                type="application/vnd.oai.openapi+json;version=3.0",
                title="OpenAPI definition",
            ),
            Link(
                href=f"{base_url}/api.html",
                rel="service-doc",
                type="text/html",
                title="API documentation",
            ),
            Link(
                href=f"{base_url}/conformance",
                rel="conformance",
                type="application/json",
                title="Conformance classes",
            ),
            Link(
                href=f"{base_url}/collections/{{collectionId}}",
                rel="data",
                type="application/json",
                title="Collection metadata (Template)",
                templated=True,
            ),
            Link(
                href=f"{base_url}/collections/{{collectionId}}/items",
                rel="data",
                type="application/geo+json",
                title="Collection items (Template)",
                templated=True,
            ),
            Link(
                href=f"{base_url}/collections/{{collectionId}}/tiles/{{tileMatrixSetId}}/{{z}}/{{x}}/{{y}}",
                rel="data",
                type="application/vnd.mapbox-vector-tile",
                title="Vector tiles (Template)",
                templated=True,
            ),
            Link(
                href=f"{base_url}/tileMatrixSets",
                rel="data",
                type="application/json",
                title="Tile matrix sets",
            ),
        ],
    )


@router.get(
    "/conformance",
    summary="Conformance classes",
    response_model=Conformance,
)
async def conformance() -> Conformance:
    """List supported OGC conformance classes."""
    return Conformance(conformsTo=CONFORMANCE_CLASSES)


@router.get(
    "/collections/{collectionId}",
    summary="Collection metadata",
    response_model=Collection,
)
async def get_collection(
    request: Request,
    layer_info: LayerInfoDep,
) -> Collection:
    """Get metadata for a specific collection."""
    metadata = await layer_service.get_layer_metadata(layer_info)
    if not metadata:
        raise HTTPException(status_code=404, detail="Collection not found")

    base_url = str(request.base_url).rstrip("/")
    collection_id = layer_info.layer_id

    links = [
        Link(
            href=f"{base_url}/collections/{collection_id}",
            rel="self",
            type="application/json",
        ),
        Link(
            href=f"{base_url}/collections/{collection_id}/items",
            rel="items",
            type="application/geo+json",
            title="Items",
        ),
        Link(
            href=f"{base_url}/collections/{collection_id}/queryables",
            rel="queryables",
            type="application/schema+json",
            title="Queryables",
        ),
    ]

    # Add tiles links if layer has geometry
    if metadata.has_geometry:
        links.extend(
            [
                Link(
                    href=f"{base_url}/collections/{collection_id}/tiles",
                    rel="tiles",
                    type="application/json",
                    title="Tiles",
                ),
                Link(
                    href=f"{base_url}/collections/{collection_id}/tiles/WebMercatorQuad/tilejson.json",
                    rel="describedby",
                    type="application/json",
                    title="TileJSON",
                ),
            ]
        )

    extent = None
    if metadata.bounds:
        extent = Extent(spatial=SpatialExtent(bbox=[metadata.bounds]))

    return Collection(
        id=collection_id,
        title=metadata.name,
        links=links,
        extent=extent,
    )


@router.get(
    "/collections/{collectionId}/queryables",
    summary="Collection queryables",
    response_model=Queryables,
)
async def get_queryables(
    request: Request,
    layer_info: LayerInfoDep,
) -> Queryables:
    """Get queryable properties for a collection."""
    metadata = await layer_service.get_layer_metadata(layer_info)
    if not metadata:
        raise HTTPException(status_code=404, detail="Collection not found")

    base_url = str(request.base_url).rstrip("/")
    collection_id = layer_info.layer_id

    # Build properties from column info, excluding hidden fields
    properties = {}
    for col in metadata.columns:
        col_name = col["name"]
        # Skip hidden fields (e.g., bbox columns)
        if col_name in settings.HIDDEN_FIELDS:
            continue
        if col_name == "geom":
            properties["geom"] = {"$ref": "https://geojson.org/schema/Geometry.json"}
        else:
            properties[col_name] = {
                "name": col_name,
                "type": col["json_type"],
            }

    return Queryables(
        title=collection_id,
        properties=properties,
        id_=f"{base_url}/collections/{collection_id}/queryables",
    )
