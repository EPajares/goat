"""Services package for GeoAPI."""

from geoapi.services.analytics_registry import analytics_registry
from geoapi.services.analytics_service import analytics_service
from geoapi.services.feature_service import FeatureService, feature_service
from geoapi.services.layer_service import LayerService, layer_service
from geoapi.services.tile_service import TileService, tile_service
from geoapi.services.tool_registry import tool_registry
from geoapi.services.windmill_client import windmill_client

__all__ = [
    # Classes
    "LayerService",
    "TileService",
    "FeatureService",
    # Singleton instances
    "analytics_registry",
    "analytics_service",
    "feature_service",
    "layer_service",
    "tile_service",
    "tool_registry",
    "windmill_client",
]
