"""Metadata router for OGC API collection and conformance endpoints."""

from typing import Any, cast
from uuid import UUID

import asyncpg
from fastapi import APIRouter, Header, HTTPException, Request, Response

from geoapi.config import settings
from geoapi.dependencies import LayerInfo, LayerInfoDep
from geoapi.ducklake_pool import ducklake_pool
from geoapi.http_cache import apply_cache_headers, build_query_etag, not_modified
from geoapi.models import (
    Collection,
    Conformance,
    Extent,
    LandingPage,
    Link,
    Queryables,
    SpatialExtent,
)
from geoapi.routers.tiles import get_layer_version
from geoapi.services.computed_columns import fetch_field_config
from geoapi.services.layer_service import layer_service

router = APIRouter(tags=["Metadata"])


def _kind_from_json_type(json_type: str, json_format: str | None = None) -> str:
    """Infer the field kind from the JSON-schema type/format for columns without explicit metadata."""
    if json_format == "date-time":
        return "datetime"
    if json_type in ("number", "integer"):
        return "number"
    if json_type == "boolean":
        return "boolean"
    return "string"


async def _load_field_config(layer_info: LayerInfo) -> dict[str, Any]:
    """Fetch the layer's field_config JSONB from PG.

    Returns an empty dict if no PG pool is initialised (dev/test path).
    Genuine connection errors propagate so the caller fails the request.
    """
    pool = layer_service._pool
    if not pool:
        return {}
    async with pool.acquire() as conn:
        return await fetch_field_config(
            cast("asyncpg.Connection[asyncpg.Record]", conn),
            UUID(layer_info.layer_id),
        )


def _apply_field_config_to_properties(
    properties: dict[str, dict[str, Any]],
    field_config: dict[str, Any],
) -> None:
    """Augment each property entry with kind, is_computed, and display_config.

    Mutates *properties* in-place. Skips geometry entries (those that have
    a ``$ref`` key instead of a ``type`` key).
    """
    for name, prop in properties.items():
        if "$ref" in prop:
            # Geometry reference entry — no field-config augmentation needed.
            continue
        entry = field_config.get(name, {})
        json_type = prop.get("type", "string")
        json_format = prop.get("format")
        prop["kind"] = entry.get("kind") or _kind_from_json_type(json_type, json_format)
        prop["is_computed"] = entry.get("is_computed", False)
        prop["display_config"] = entry.get("display_config", {})
        if entry.get("kind") == "formula":
            # The expression (for the editor) and the result kind (drives
            # value formatting and formatting options in the frontend).
            prop["formula"] = entry.get("formula")
            prop["output_kind"] = entry.get("output_kind", "string")


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
    response: Response,
    layer_info: LayerInfoDep,
    if_none_match: str | None = Header(default=None, alias="if-none-match"),
) -> Collection | Response:
    """Get metadata for a specific collection."""
    etag = build_query_etag(
        layer_info.layer_id,
        get_layer_version(layer_info.layer_id),
        ducklake_pool.pinned_snapshot_id,
        params={"kind": "collection"},
    )
    if cached := not_modified(if_none_match, etag):
        return cached

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

    apply_cache_headers(response, etag)
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
    response: Response,
    layer_info: LayerInfoDep,
    if_none_match: str | None = Header(default=None, alias="if-none-match"),
) -> Queryables | Response:
    """Get queryable properties for a collection."""
    # field_config lives in PG, not DuckLake: editing it (kind, formula,
    # display_config) rotates neither the layer version nor the pinned
    # snapshot, so it must be part of the fingerprint itself — otherwise
    # a 304 would serve stale field metadata forever.
    field_config = await _load_field_config(layer_info)
    etag = build_query_etag(
        layer_info.layer_id,
        get_layer_version(layer_info.layer_id),
        ducklake_pool.pinned_snapshot_id,
        params={"kind": "queryables", "field_config": field_config},
    )
    if cached := not_modified(if_none_match, etag):
        return cached

    metadata = await layer_service.get_layer_metadata(layer_info)
    if not metadata:
        raise HTTPException(status_code=404, detail="Collection not found")

    base_url = str(request.base_url).rstrip("/")
    collection_id = layer_info.layer_id

    # Build properties from column info, excluding hidden fields
    properties: dict[str, dict[str, Any]] = {}
    for col in metadata.columns:
        col_name = col["name"]
        # Skip hidden fields (e.g., bbox columns)
        if col_name in settings.HIDDEN_FIELDS:
            continue
        if col_name == "geom":
            properties["geom"] = {"$ref": "https://geojson.org/schema/Geometry.json"}
        else:
            prop: dict[str, Any] = {
                "name": col_name,
                "type": col["json_type"],
            }
            if col.get("format"):
                prop["format"] = col["format"]
            properties[col_name] = prop

    # Augment each property with field-config metadata (kind, is_computed, display_config).
    _apply_field_config_to_properties(properties, field_config)

    apply_cache_headers(response, etag)
    return Queryables(
        title=collection_id,
        properties=properties,
        id_=f"{base_url}/collections/{collection_id}/queryables",
    )
