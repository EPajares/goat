"""Routers package for GeoAPI."""

from geoapi.routers.features import router as features_router
from geoapi.routers.metadata import router as metadata_router
from geoapi.routers.tiles import router as tiles_router

__all__ = ["tiles_router", "features_router", "metadata_router"]
