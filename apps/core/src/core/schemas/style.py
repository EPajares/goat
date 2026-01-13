import random
from typing import Any, Dict, List

from core.db.models.layer import FeatureGeometryType
from core.schemas.colors import ColorRangeType, color_ranges, diverging_colors
from core.utils import hex_to_rgb

# TODO: Add Basic pydantic validation
default_style_settings = {
    "min_zoom": 1,
    "max_zoom": 22,
    "visibility": True,
}

default_point_style_settings = {
    **default_style_settings,
    "filled": True,
    "fixed_radius": False,
    "radius_range": [0, 10],
    "radius_scale": "linear",
    "radius": 5,
    "opacity": 1,
    "stroked": False,
}

default_line_style_settings = {
    **default_style_settings,
    "filled": True,
    "opacity": 1,
    "stroked": True,
    "stroke_width": 7,
    "stroke_width_range": [0, 10],
    "stroke_width_scale": "linear",
}

default_polygon_style_settings = {
    **default_style_settings,
    "filled": True,
    "opacity": 0.8,
    "stroked": False,
    "stroke_width": 3,
    "stroke_width_range": [0, 10],
    "stroke_width_scale": "linear",
    "stroke_color": [217, 25, 85],
}


def get_base_style(feature_geometry_type: FeatureGeometryType) -> Dict[str, Any]:
    """Return the base style for the given feature geometry type and tool type."""

    color = hex_to_rgb(random.choice(diverging_colors["Spectral"][-1]["colors"]))
    if feature_geometry_type == FeatureGeometryType.point:
        return {
            "color": color,
            **default_point_style_settings,
        }
    elif feature_geometry_type == FeatureGeometryType.line:
        return {
            "color": color,
            **default_line_style_settings,
            "stroke_color": color,
        }
    elif feature_geometry_type == FeatureGeometryType.polygon:
        return {
            **default_polygon_style_settings,
            "color": color,
        }


def get_tool_style_with_breaks(
    feature_geometry_type: FeatureGeometryType,
    color_field: Dict[str, Any],
    color_scale_breaks: Dict[str, Any],
    color_range_type: ColorRangeType,
) -> Dict[str, Any]:
    """Return the style for the given feature geometry type and property settings."""

    index_color_range = len(color_scale_breaks["breaks"]) - 2
    color_sequence = color_ranges.get(color_range_type)
    if not color_sequence:
        raise ValueError(f"Invalid color range type: {color_range_type}")
    random_color_range_key = random.choice(list(color_sequence.keys()))
    random_color_range = color_ranges[color_range_type][random_color_range_key][
        index_color_range
    ]
    color = hex_to_rgb(random.choice(random_color_range["colors"]))

    if feature_geometry_type == FeatureGeometryType.point:
        return {
            **default_point_style_settings,
            "color": color,
            "color_field": color_field,
            "color_range": random_color_range,
            "color_scale": "quantile",
            "color_scale_breaks": color_scale_breaks,
        }
    elif feature_geometry_type == FeatureGeometryType.polygon:
        return {
            **default_polygon_style_settings,
            "color_field": color_field,
            "color_range": random_color_range,
            "color_scale": "quantile",
            "color_scale_breaks": color_scale_breaks,
            "stroke_color_range": random_color_range,
            "stroke_color_scale": "quantile",
        }
    elif feature_geometry_type == FeatureGeometryType.line:
        return {
            **default_line_style_settings,
            "color": color,
            "color_range": random_color_range,
            "color_scale": "quantile",
            "stroke_color_scale_breaks": color_scale_breaks,
            "stroke_color_field": color_field,
            "stroke_color": color,
            "stroke_color_range": random_color_range,
            "stroke_color_scale": "quantile",
        }


def get_tool_style_ordinal(
    feature_geometry_type: FeatureGeometryType,
    color_range_type: ColorRangeType,
    color_field: Dict[str, Any],
    unique_values: List[str],
) -> Dict[str, Any]:
    """Return the style for the given feature geometry type and property settings."""

    index_color_range = len(unique_values) - 3
    color_sequence = color_ranges.get(color_range_type)
    if not color_sequence:
        raise ValueError(f"Invalid color range type: {color_range_type}")
    random_color_range_key = random.choice(list(color_sequence.keys()))
    random_color_range = color_ranges[color_range_type][random_color_range_key][
        index_color_range
    ]
    # Create color map
    color_map = []
    cnt = 0
    # Sort unique values and try casting to int of possible and sort. Return it unchanged if it is not possible to cast to int
    unique_values = sorted(unique_values, key=lambda x: int(x) if x.isdigit() else x)
    for value in unique_values:
        color_map.append([[str(value)], random_color_range["colors"][cnt]])
        cnt += 1

    color_range = {
        "name": "Custom",
        "type": "custom",
        "colors": random_color_range["colors"],
        "category": "Custom",
        "color_map": color_map,
    }

    if feature_geometry_type == FeatureGeometryType.point:
        return {
            **default_point_style_settings,
            "color": hex_to_rgb(random_color_range["colors"][0]),
            "color_field": color_field,
            "color_range": color_range,
            "color_scale": "ordinal",
        }
    elif feature_geometry_type == FeatureGeometryType.polygon:
        return {
            **default_polygon_style_settings,
            "color": hex_to_rgb(random_color_range["colors"][0]),
            "color_field": color_field,
            "color_range": color_range,
            "color_scale": "ordinal",
        }
    elif feature_geometry_type == FeatureGeometryType.line:
        return {
            **default_line_style_settings,
            "color": hex_to_rgb(random_color_range["colors"][0]),
            "color_field": color_field,
            "color_range": color_range,
            "color_scale": "ordinal",
        }
