"""Default style generation for tool output layers.

Mirrors the style logic from core.schemas.style to generate
consistent default layer properties.
"""

import random
from enum import Enum
from typing import Any

# Spectral color palette (from core.schemas.colors)
# Filtered to exclude light yellows/greens that are hard to see on maps
SPECTRAL_COLORS = [
    "#9e0142",  # dark magenta
    "#d53e4f",  # red
    "#f46d43",  # orange
    "#fdae61",  # light orange
    "#66c2a5",  # teal
    "#3288bd",  # blue
    "#5e4fa2",  # purple
]

# Sequential color ranges for heatmaps
SEQUENTIAL_COLOR_RANGES = {
    "Mint": {
        "name": "Mint",
        "type": "sequential",
        "category": "ColorBrewer",
        "colors": [
            "#e4f1e1",
            "#c0dfd1",
            "#93cfb5",
            "#63b598",
            "#3a9c7c",
            "#1a8060",
            "#006344",
        ],
    },
    "BluYl": {
        "name": "BluYl",
        "type": "sequential",
        "category": "ColorBrewer",
        "colors": [
            "#f7feae",
            "#b7e6a5",
            "#7ccba2",
            "#46aea0",
            "#089099",
            "#00718b",
            "#045275",
        ],
    },
    "Teal": {
        "name": "Teal",
        "type": "sequential",
        "category": "ColorBrewer",
        "colors": [
            "#d1eeea",
            "#a8dbd9",
            "#85c4c9",
            "#68abb8",
            "#4f90a6",
            "#3b738f",
            "#2a5674",
        ],
    },
    "Emrld": {
        "name": "Emrld",
        "type": "sequential",
        "category": "ColorBrewer",
        "colors": [
            "#d3f2a3",
            "#97e196",
            "#6cc08b",
            "#4c9b82",
            "#217a79",
            "#105965",
            "#074050",
        ],
    },
}


class ToolStyleType(str, Enum):
    """Tool types that have custom default styles."""

    heatmap_gravity = "heatmap_gravity"
    heatmap_closest_average = "heatmap_closest_average"
    heatmap_connectivity = "heatmap_connectivity"
    catchment_area = "catchment_area"
    isochrone = "isochrone"
    oev_gueteklasse = "oev_gueteklassen"


# Tool-specific style configurations
TOOL_STYLE_CONFIG: dict[str, dict[str, Any]] = {
    "heatmap_gravity": {
        "color_field": {"name": "accessibility", "type": "number"},
        "color_scale": "quantile",
        "color_range_type": "sequential",
    },
    "heatmap_closest_average": {
        "color_field": {"name": "total_accessibility", "type": "number"},
        "color_scale": "quantile",
        "color_range_type": "sequential",
    },
    "heatmap_connectivity": {
        "color_field": {"name": "accessibility", "type": "number"},
        "color_scale": "quantile",
        "color_range_type": "sequential",
    },
    "catchment_area": {
        "color_field": {"name": "travel_cost", "type": "number"},
        "color_scale": "ordinal",
        "color_range_type": "sequential",
    },
    "isochrone": {
        "color_field": {"name": "travel_cost", "type": "number"},
        "color_scale": "ordinal",
        "color_range_type": "sequential",
    },
}

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


def get_tool_style(
    tool_type: str,
    geometry_type: str | None = "polygon",
    color_scale_breaks: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Generate style for a specific tool type with color scale support.

    Args:
        tool_type: The tool type (e.g., "heatmap_gravity", "catchment_area")
        geometry_type: Normalized geometry type ("point", "line", "polygon")
        color_scale_breaks: Optional pre-computed break values for quantile scales
            Format: {"min": 0, "max": 100, "mean": 50, "breaks": [20, 40, 60, 80]}

    Returns:
        Style dict with color field and scale configuration
    """
    # Get base style for geometry type
    base_style = get_default_style(geometry_type)

    # Check if we have a specific config for this tool
    tool_config = TOOL_STYLE_CONFIG.get(tool_type)
    if not tool_config:
        return base_style

    # Pick a random sequential color range
    color_range_key = random.choice(list(SEQUENTIAL_COLOR_RANGES.keys()))
    color_range = SEQUENTIAL_COLOR_RANGES[color_range_key]

    # Build the style with color field configuration
    style = {
        **base_style,
        "color_field": tool_config["color_field"],
        "color_range": color_range,
        "color_scale": tool_config["color_scale"],
    }

    # Add color scale breaks if provided
    if color_scale_breaks:
        style["color_scale_breaks"] = color_scale_breaks

    return style


def get_ordinal_style(
    color_field_name: str = "travel_cost",
    color_scale_breaks: dict[str, Any] | None = None,
    color_range_name: str | None = None,
) -> dict[str, Any]:
    """Generate ordinal color scale style for catchment areas.

    Uses ordinal scale where each discrete value maps to a color,
    suitable for isochrone/catchment area visualization.

    Args:
        color_field_name: Name of the field to use for coloring
        color_scale_breaks: Break values defining color boundaries
        color_range_name: Optional specific color range name

    Returns:
        Style dict configured for ordinal visualization
    """
    # Default color range for catchment areas (orange-red gradient)
    sunset_range = {
        "name": "Sunset",
        "type": "sequential",
        "category": "ColorBrewer",
        "colors": [
            "#f3e79b",  # Light yellow
            "#fac484",  # Light orange
            "#f8a07e",  # Orange
            "#eb7f86",  # Salmon
            "#ce6693",  # Pink
            "#a059a0",  # Purple
            "#5c53a5",  # Dark purple
        ],
    }

    # Use specified color range or sunset default
    if color_range_name and color_range_name in SEQUENTIAL_COLOR_RANGES:
        color_range = SEQUENTIAL_COLOR_RANGES[color_range_name]
    elif color_range_name == "Sunset":
        color_range = sunset_range
    else:
        color_range = sunset_range

    style = {
        **DEFAULT_POLYGON_STYLE,
        "color": hex_to_rgb(color_range["colors"][3]),  # Middle color as base
        "color_field": {"name": color_field_name, "type": "number"},
        "color_range": color_range,
        "color_scale": "ordinal",
    }

    if color_scale_breaks:
        style["color_scale_breaks"] = color_scale_breaks

    return style


def get_heatmap_style(
    color_field_name: str = "accessibility",
    color_scale_breaks: dict[str, Any] | None = None,
    color_range_name: str | None = None,
) -> dict[str, Any]:
    """Generate heatmap-specific style with quantile color scale.

    Args:
        color_field_name: Name of the field to use for coloring
        color_scale_breaks: Optional pre-computed break values
        color_range_name: Optional specific color range name (Mint, BluYl, Teal, Emrld)
                         If None, picks randomly

    Returns:
        Style dict configured for heatmap visualization
    """
    # Use specified color range or pick randomly
    if color_range_name and color_range_name in SEQUENTIAL_COLOR_RANGES:
        color_range = SEQUENTIAL_COLOR_RANGES[color_range_name]
    else:
        color_range_key = random.choice(list(SEQUENTIAL_COLOR_RANGES.keys()))
        color_range = SEQUENTIAL_COLOR_RANGES[color_range_key]

    style = {
        **DEFAULT_POLYGON_STYLE,
        "color": hex_to_rgb(color_range["colors"][3]),  # Middle color as base
        "color_field": {"name": color_field_name, "type": "number"},
        "color_range": color_range,
        "color_scale": "quantile",
        # For polygons, also set stroke color scale to match
        "stroke_color_range": color_range,
        "stroke_color_scale": "quantile",
    }

    if color_scale_breaks:
        style["color_scale_breaks"] = color_scale_breaks

    return style


# ÖV-Güteklassen style configuration
OEV_GUETEKLASSEN_COLOR_MAP = {
    "A": "#199741",  # Dark green - best quality
    "B": "#8BCC62",  # Light green
    "C": "#DCF09E",  # Yellow-green
    "D": "#FFDF9A",  # Yellow
    "E": "#F69053",  # Orange
    "F": "#E4696A",  # Red - worst quality
}


def get_oev_gueteklassen_style() -> dict[str, Any]:
    """Generate style for ÖV-Güteklassen (PT quality classes) output.

    Uses ordinal color scale with A-F categories representing
    public transport accessibility quality from best (A) to worst (F).

    Returns:
        Style dict configured for ÖV-Güteklassen visualization
    """
    colors = list(OEV_GUETEKLASSEN_COLOR_MAP.values())
    color_map = [
        [[class_name], color]
        for class_name, color in OEV_GUETEKLASSEN_COLOR_MAP.items()
    ]

    return {
        **DEFAULT_POLYGON_STYLE,
        "color": hex_to_rgb(colors[2]),  # Default to middle color
        "opacity": 0.8,
        "stroked": False,
        "color_field": {"name": "pt_class_label", "type": "string"},
        "color_range": {
            "name": "Custom",
            "type": "custom",
            "colors": colors,
            "category": "Custom",
            "color_map": color_map,
        },
        "color_scale": "ordinal",
    }


# Station category color map (1-7 categories, 999 = no service)
OEV_GUETEKLASSEN_STATION_COLOR_MAP = {
    "1": "#000000",  # Category I - black (best)
    "2": "#000000",  # Category II
    "3": "#000000",  # Category III
    "4": "#000000",  # Category IV
    "5": "#000000",  # Category V
    "6": "#000000",  # Category VI
    "7": "#000000",  # Category VII (worst with service)
    "999": "#717171",  # No service - gray
}


def get_oev_gueteklassen_stations_style() -> dict[str, Any]:
    """Generate style for ÖV-Güteklassen station points.

    Uses ordinal color scale with station categories 1-7 and 999 (no service).

    Returns:
        Style dict configured for station point visualization
    """
    colors = list(OEV_GUETEKLASSEN_STATION_COLOR_MAP.values())
    color_map = [
        [[cat], color] for cat, color in OEV_GUETEKLASSEN_STATION_COLOR_MAP.items()
    ]

    return {
        **DEFAULT_POINT_STYLE,
        "color": hex_to_rgb("#000000"),
        "radius": 3,
        "opacity": 1,
        "color_field": {"name": "station_category", "type": "number"},
        "color_range": {
            "name": "Custom",
            "type": "custom",
            "colors": colors,
            "category": "Custom",
            "color_map": color_map,
        },
        "color_scale": "ordinal",
        "marker_size": 10,
        "fixed_radius": False,
    }
