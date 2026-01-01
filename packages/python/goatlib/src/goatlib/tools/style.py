"""Default style generation for tool output layers.

Mirrors the style logic from core.schemas.style to generate
consistent default layer properties.
"""

import random
from typing import Any

# Spectral color palette (from core.schemas.colors)
SPECTRAL_COLORS = [
    "#9e0142",
    "#d53e4f",
    "#f46d43",
    "#fdae61",
    "#fee08b",
    "#ffffbf",
    "#e6f598",
    "#abdda4",
    "#66c2a5",
    "#3288bd",
    "#5e4fa2",
]

DEFAULT_STYLE_SETTINGS = {
    "min_zoom": 1,
    "max_zoom": 22,
    "visibility": True,
}

DEFAULT_POINT_STYLE = {
    **DEFAULT_STYLE_SETTINGS,
    "filled": True,
    "fixed_radius": False,
    "radius_range": [0, 10],
    "radius_scale": "linear",
    "radius": 5,
    "opacity": 1,
    "stroked": False,
}

DEFAULT_LINE_STYLE = {
    **DEFAULT_STYLE_SETTINGS,
    "filled": True,
    "opacity": 1,
    "stroked": True,
    "stroke_width": 7,
    "stroke_width_range": [0, 10],
    "stroke_width_scale": "linear",
}

DEFAULT_POLYGON_STYLE = {
    **DEFAULT_STYLE_SETTINGS,
    "filled": True,
    "opacity": 0.8,
    "stroked": False,
    "stroke_width": 3,
    "stroke_width_range": [0, 10],
    "stroke_width_scale": "linear",
    "stroke_color": [217, 25, 85],
}


def hex_to_rgb(hex_color: str) -> list[int]:
    """Convert hex color to RGB list.

    Args:
        hex_color: Color in hex format (e.g., "#9e0142")

    Returns:
        RGB values as [r, g, b]
    """
    hex_color = hex_color.lstrip("#")
    return [int(hex_color[i : i + 2], 16) for i in (0, 2, 4)]


def get_default_style(geometry_type: str | None) -> dict[str, Any]:
    """Generate default layer style based on geometry type.

    Args:
        geometry_type: Normalized geometry type ("point", "line", "polygon")

    Returns:
        Style dict compatible with GOAT layer properties
    """
    # Pick a random color from Spectral palette
    color = hex_to_rgb(random.choice(SPECTRAL_COLORS))

    if geometry_type == "point":
        return {
            "color": color,
            **DEFAULT_POINT_STYLE,
        }
    elif geometry_type == "line":
        return {
            "color": color,
            "stroke_color": color,
            **DEFAULT_LINE_STYLE,
        }
    elif geometry_type == "polygon":
        return {
            "color": color,
            **DEFAULT_POLYGON_STYLE,
        }
    else:
        # Fallback for unknown/null geometry
        return {
            "color": color,
            **DEFAULT_STYLE_SETTINGS,
        }
