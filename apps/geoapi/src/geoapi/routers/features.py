"""Features router for OGC Features API endpoints."""

import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, Path, Query, Request

from geoapi.dependencies import (
    BBoxDep,
    CqlFilterDep,
    LayerInfoDep,
    LimitDep,
    OffsetDep,
    PropertiesDep,
)
from geoapi.models import Feature, FeatureCollection, Link
from geoapi.services.feature_service import feature_service
from geoapi.services.layer_service import layer_service

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Features"])


@router.get(
    "/collections/{collectionId}/items",
    summary="Get features",
    response_model=FeatureCollection,
)
async def get_features(
    request: Request,
    layer_info: LayerInfoDep,
    limit: LimitDep,
    offset: OffsetDep,
    bbox: BBoxDep = None,
    properties: PropertiesDep = None,
    cql_filter: CqlFilterDep = None,
    ids: Optional[str] = Query(default=None, description="Comma-separated feature IDs"),
    sortby: Optional[str] = Query(
        default=None, description="Sort column (prefix with - for desc)"
    ),
) -> FeatureCollection:
    """Get features from a collection.

    Supports:
    - Pagination with limit/offset
    - Bounding box filtering
    - Property selection
    - CQL2 filtering
    - ID filtering
    - Sorting
    """
    # Get layer metadata
    logger.debug("Getting features for layer_info: %s", layer_info)
    metadata = await layer_service.get_layer_metadata(layer_info)
    if not metadata:
        raise HTTPException(status_code=404, detail="Collection not found")

    column_names = metadata.column_names
    geometry_column = metadata.geometry_column or "geometry"
    has_geometry = metadata.has_geometry
    logger.debug(
        "Layer %s: columns=%s, geometry_column=%s, has_geometry=%s",
        layer_info.layer_id,
        column_names,
        geometry_column,
        has_geometry,
    )

    # Parse IDs
    id_list = None
    if ids:
        id_list = [id.strip() for id in ids.split(",")]

    # Get features
    features, total_count = feature_service.get_features(
        layer_info=layer_info,
        limit=limit,
        offset=offset,
        bbox=bbox,
        properties=properties,
        cql_filter=cql_filter,
        column_names=column_names,
        sortby=sortby,
        ids=id_list,
        geometry_column=geometry_column,
        has_geometry=has_geometry,
    )

    # Build links
    base_url = str(request.base_url).rstrip("/")
    collection_id = layer_info.layer_id

    links = [
        Link(
            href=f"{base_url}/collections/{collection_id}/items",
            rel="self",
            type="application/geo+json",
        ),
        Link(
            href=f"{base_url}/collections/{collection_id}",
            rel="collection",
            type="application/json",
        ),
    ]

    # Add pagination links
    if offset + limit < total_count:
        next_offset = offset + limit
        links.append(
            Link(
                href=f"{base_url}/collections/{collection_id}/items?limit={limit}&offset={next_offset}",
                rel="next",
                type="application/geo+json",
                title="Next page",
            )
        )

    if offset > 0:
        prev_offset = max(0, offset - limit)
        links.append(
            Link(
                href=f"{base_url}/collections/{collection_id}/items?limit={limit}&offset={prev_offset}",
                rel="prev",
                type="application/geo+json",
                title="Previous page",
            )
        )

    # Convert features to Feature models with links
    feature_models = []
    for f in features:
        feature_links = [
            Link(
                href=f"{base_url}/collections/{collection_id}/items/{f['id']}",
                rel="self",
                type="application/geo+json",
            ),
            Link(
                href=f"{base_url}/collections/{collection_id}",
                rel="collection",
                type="application/json",
            ),
        ]
        feature_models.append(
            Feature(
                id=f["id"],
                geometry=f["geometry"],
                properties=f["properties"],
                links=feature_links,
            )
        )

    return FeatureCollection(
        features=feature_models,
        links=links,
        numberMatched=total_count,
        numberReturned=len(features),
    )


@router.get(
    "/collections/{collectionId}/items/{itemId}",
    summary="Get feature by ID",
    response_model=Feature,
)
async def get_feature(
    request: Request,
    layer_info: LayerInfoDep,
    itemId: str = Path(..., description="Feature ID"),
    properties: PropertiesDep = None,
) -> Feature:
    """Get a single feature by ID."""
    # Get layer metadata
    metadata = await layer_service.get_layer_metadata(layer_info)
    if not metadata:
        raise HTTPException(status_code=404, detail="Collection not found")

    geometry_column = metadata.geometry_column or "geometry"
    has_geometry = metadata.has_geometry

    # Get feature
    feature = feature_service.get_feature_by_id(
        layer_info=layer_info,
        feature_id=itemId,
        properties=properties,
        geometry_column=geometry_column,
        has_geometry=has_geometry,
    )

    if not feature:
        raise HTTPException(status_code=404, detail="Feature not found")

    # Build links
    base_url = str(request.base_url).rstrip("/")
    collection_id = layer_info.layer_id

    links = [
        Link(
            href=f"{base_url}/collections/{collection_id}/items/{itemId}",
            rel="self",
            type="application/geo+json",
        ),
        Link(
            href=f"{base_url}/collections/{collection_id}",
            rel="collection",
            type="application/json",
        ),
    ]

    return Feature(
        id=feature["id"],
        geometry=feature["geometry"],
        properties=feature["properties"],
        links=links,
    )
