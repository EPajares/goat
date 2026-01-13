"""Utility functions for goatlib.

Note: Layer utilities (normalize_layer_id, get_schema_for_layer, etc.)
are available via direct import from goatlib.utils.layer to avoid
importing cachetools at module load time.
"""

from goatlib.utils.helper import UNIT_TO_METERS

__all__ = [
    "UNIT_TO_METERS",
]
