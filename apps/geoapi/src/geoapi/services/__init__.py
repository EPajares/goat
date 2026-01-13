"""Services package for GeoAPI."""

from geoapi.services.feature_service import FeatureService, feature_service
from geoapi.services.layer_service import LayerService, layer_service
from geoapi.services.tile_service import TileService, tile_service

__all__ = [
    # Classes
    "LayerService",
    "TileService",
    "FeatureService",
    # Singleton instances
    "feature_service",
    "layer_service",
    "tile_service",
]
