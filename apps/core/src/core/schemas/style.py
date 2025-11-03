import random
from typing import Any, Dict, List

from core.db.models.layer import FeatureGeometryType
from core.schemas.colors import ColorRangeType, color_ranges, diverging_colors
from core.schemas.toolbox_base import DefaultResultLayerName
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


style_oev_gueteklassen_polygon = {
    "color": [237, 248, 251],
    "filled": True,
    "opacity": 0.8,
    "stroked": False,
    "max_zoom": 22,
    "min_zoom": 1,
    "visibility": True,
    "color_field": {"name": "pt_class", "type": "string"},
    "color_range": {
        "name": "Custom",
        "type": "custom",
        "colors": ["#199741", "#8BCC62", "#DCF09E", "#FFDF9A", "#F69053", "#E4696A"],
        "category": "Custom",
        "color_map": [
            [["A"], "#199741"],
            [["B"], "#8BCC62"],
            [["C"], "#DCF09E"],
            [["D"], "#FFDF9A"],
            [["E"], "#F69053"],
            [["F"], "#E4696A"],
        ],
    },
    "color_scale": "ordinal",
    "stroke_color": [217, 25, 85],
    "stroke_width": 3,
    "stroke_color_range": {
        "name": "Global Warming",
        "type": "sequential",
        "colors": ["#5A1846", "#900C3F", "#C70039", "#E3611C", "#F1920E", "#FFC300"],
        "category": "Uber",
    },
    "stroke_color_scale": "quantile",
    "stroke_width_range": [0, 10],
    "stroke_width_scale": "linear",
}

style_oev_gueteklassen_point = {
    "color": [255, 247, 251],
    "filled": True,
    "radius": 3,
    "opacity": 1,
    "stroked": False,
    "max_zoom": 22,
    "min_zoom": 1,
    "visibility": True,
    "color_field": {"name": "station_category", "type": "number"},
    "color_range": {
        "name": "Custom",
        "type": "custom",
        "colors": [
            "#000000",
            "#000000",
            "#000000",
            "#000000",
            "#000000",
            "#000000",
            "#000000",
            "#717171",
        ],
        "category": "Custom",
        "color_map": [
            [["1"], "#000000"],
            [["2"], "#000000"],
            [["3"], "#000000"],
            [["4"], "#000000"],
            [["5"], "#000000"],
            [["6"], "#000000"],
            [["7"], "#000000"],
            [["999"], "#717171"],
        ],
    },
    "color_scale": "ordinal",
    "marker_size": 10,
    "fixed_radius": False,
    "radius_range": [0, 10],
    "radius_scale": "linear",
    "stroke_color": [225, 49, 106],
    "stroke_width": 2,
    "custom_marker": False,
    "marker_size_range": [0, 10],
    "color_scale_breaks": {
        "max": 999,
        "min": 1,
        "mean": 108.53644963828603,
        "breaks": [3, 4, 4, 5, 5, 6, 7],
    },
    "stroke_color_range": {
        "name": "Global Warming",
        "type": "sequential",
        "colors": ["#5A1846", "#900C3F", "#C70039", "#E3611C", "#F1920E", "#FFC300"],
        "category": "Uber",
    },
    "stroke_color_scale": "quantile",
    "stroke_width_range": [0, 10],
    "stroke_width_scale": "linear",
}

style_starting = {
    "color": [0, 0, 0],
    "filled": True,
    "marker": {
        "url": "https://assets.plan4better.de/icons/maki/foundation-marker.svg",
        "name": "foundation-marker",
    },
    "radius": 8,
    "opacity": 1,
    "stroked": False,
    "max_zoom": 22,
    "min_zoom": 1,
    "visibility": True,
    "color_range": {
        "name": "Global Warming",
        "type": "sequential",
        "colors": ["#5A1846", "#900C3F", "#C70039", "#E3611C", "#F1920E", "#FFC300"],
        "category": "Uber",
    },
    "color_scale": "quantile",
    "marker_size": 40,
    "fixed_radius": False,
    "radius_range": [0, 10],
    "radius_scale": "linear",
    "stroke_color": [225, 49, 106],
    "stroke_width": 2,
    "custom_marker": True,
    "marker_anchor": "bottom",
    "marker_offset": [0, 0],
    "marker_size_range": [0, 10],
    "stroke_color_range": {
        "name": "Global Warming",
        "type": "sequential",
        "colors": ["#5A1846", "#900C3F", "#C70039", "#E3611C", "#F1920E", "#FFC300"],
        "category": "Uber",
    },
    "stroke_color_scale": "quantile",
    "stroke_width_range": [0, 10],
    "stroke_width_scale": "linear",
}

style_nearby_station = {
    "color": [239, 101, 72],
    "filled": True,
    "radius": 5,
    "opacity": 1,
    "stroked": False,
    "max_zoom": 22,
    "min_zoom": 1,
    "visibility": True,
    "color_field": {"name": "access_time", "type": "number"},
    "color_range": {
        "name": "Uber Viz Diverging 2.5",
        "type": "diverging",
        "colors": [
            "#00939C",
            "#3EADB3",
            "#7CC7CB",
            "#BAE1E2",
            "#F8C0AA",
            "#E68F71",
            "#D45F39",
            "#C22E00",
        ],
        "category": "Uber",
    },
    "color_scale": "quantile",
    "marker_size": 30,
    "fixed_radius": False,
    "marker_field": {"name": "dominant_mode", "type": "string"},
    "radius_range": [0, 10],
    "radius_scale": "linear",
    "stroke_color": [225, 49, 106],
    "stroke_width": 2,
    "custom_marker": True,
    "marker_mapping": [
        [
            ["rail"],
            {
                "url": "https://assets.plan4better.de/icons/maki/rail-metro.svg",
                "name": "rail-metro",
            },
        ],
        [
            ["tram"],
            {
                "url": "https://assets.plan4better.de/icons/maki/rail-light.svg",
                "name": "rail-light",
            },
        ],
        [
            ["bus"],
            {"url": "https://assets.plan4better.de/icons/maki/bus.svg", "name": "bus"},
        ],
        [
            ["metro"],
            {
                "url": "https://assets.plan4better.de/icons/maki/rail.svg",
                "name": "rail",
            },
        ],
    ],
    "marker_size_range": [0, 10],
    "color_scale_breaks": {
        "max": 15,
        "min": 3,
        "mean": 9.89,
        "breaks": [6, 8, 9, 10, 11, 12, 13],
    },
    "stroke_color_range": {
        "name": "Global Warming",
        "type": "sequential",
        "colors": ["#5A1846", "#900C3F", "#C70039", "#E3611C", "#F1920E", "#FFC300"],
        "category": "Uber",
    },
    "stroke_color_scale": "quantile",
    "stroke_width_range": [0, 10],
    "stroke_width_scale": "linear",
}

custom_styles = {
    DefaultResultLayerName.oev_gueteklasse: style_oev_gueteklassen_polygon,
    DefaultResultLayerName.oev_gueteklasse_station: style_oev_gueteklassen_point,
    DefaultResultLayerName.catchment_area_starting_points: style_starting,
    DefaultResultLayerName.nearby_station_access_starting_points: style_starting,
    DefaultResultLayerName.nearby_station_access: style_nearby_station,
}
