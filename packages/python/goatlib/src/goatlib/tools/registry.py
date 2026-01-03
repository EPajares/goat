"""Centralized tool registry for GOAT tools.

This module provides a single source of truth for all tool definitions.
GeoAPI and other services can import from here instead of duplicating
tool registration logic.

Example:
    from goatlib.tools.registry import TOOL_REGISTRY, ToolDefinition

    # Get all tools
    for tool in TOOL_REGISTRY:
        print(f"{tool.name}: {tool.description}")

    # Find a specific tool
    buffer_tool = next(t for t in TOOL_REGISTRY if t.name == "buffer")
"""

from dataclasses import dataclass
from typing import TYPE_CHECKING, Self

if TYPE_CHECKING:
    from goatlib.tools.schemas import ToolInputBase


@dataclass(frozen=True)
class ToolDefinition:
    """Definition of a GOAT tool for registration.

    Attributes:
        name: Short lowercase name used as process ID (e.g., "buffer")
        display_name: Human-readable name (e.g., "Buffer")
        description: Short description for API docs
        module_path: Python module path (e.g., "goatlib.tools.buffer")
        params_class_name: Name of the Params class in the module
        windmill_path: Windmill script path (e.g., "f/goat/buffer")
        category: Tool category for grouping (e.g., "geoprocessing", "data")
        keywords: Search keywords for discovery
        toolbox_hidden: If True, hide from toolbox UI (still available via API)
        docs_path: Path to documentation (appended to docs base URL)
    """

    name: str
    display_name: str
    description: str
    module_path: str
    params_class_name: str
    windmill_path: str
    category: str = "geoprocessing"
    keywords: tuple[str, ...] = ()
    toolbox_hidden: bool = False
    docs_path: str | None = None

    def get_params_class(self: Self) -> type["ToolInputBase"]:
        """Dynamically import and return the params class."""
        import importlib

        module = importlib.import_module(self.module_path)
        return getattr(module, self.params_class_name)


# Central registry of all GOAT tools
TOOL_REGISTRY: tuple[ToolDefinition, ...] = (
    ToolDefinition(
        name="buffer",
        display_name="Buffer",
        description="Create buffer zones around features",
        module_path="goatlib.tools.buffer",
        params_class_name="BufferToolParams",
        windmill_path="f/goat/buffer",
        category="geoprocessing",
        keywords=("geoprocessing", "buffer", "geometry"),
        docs_path="/toolbox/geoprocessing/buffer",
    ),
    ToolDefinition(
        name="clip",
        display_name="Clip",
        description="Clip features using overlay geometry",
        module_path="goatlib.tools.clip",
        params_class_name="ClipToolParams",
        windmill_path="f/goat/clip",
        category="geoprocessing",
        keywords=("geoprocessing", "clip", "overlay"),
    ),
    ToolDefinition(
        name="centroid",
        display_name="Centroid",
        description="Compute centroid points for features",
        module_path="goatlib.tools.centroid",
        params_class_name="CentroidToolParams",
        windmill_path="f/goat/centroid",
        category="geoprocessing",
        keywords=("geoprocessing", "centroid", "point"),
    ),
    ToolDefinition(
        name="intersection",
        display_name="Intersection",
        description="Compute the geometric intersection of features from two layers",
        module_path="goatlib.tools.intersection",
        params_class_name="IntersectionToolParams",
        windmill_path="f/goat/intersection",
        category="geoprocessing",
        keywords=("geoprocessing", "intersection", "overlay"),
    ),
    ToolDefinition(
        name="union",
        display_name="Union",
        description="Compute the geometric union of features from two layers",
        module_path="goatlib.tools.union",
        params_class_name="UnionToolParams",
        windmill_path="f/goat/union",
        category="geoprocessing",
        keywords=("geoprocessing", "union", "overlay", "merge"),
    ),
    ToolDefinition(
        name="difference",
        display_name="Difference",
        description="Compute the geometric difference between features from two layers",
        module_path="goatlib.tools.difference",
        params_class_name="DifferenceToolParams",
        windmill_path="f/goat/difference",
        category="geoprocessing",
        keywords=("geoprocessing", "difference", "overlay", "subtract"),
    ),
    ToolDefinition(
        name="origin_destination",
        display_name="Origin-Destination",
        description="Create origin-destination lines and points from geometry and OD matrix",
        module_path="goatlib.tools.origin_destination",
        params_class_name="OriginDestinationToolParams",
        windmill_path="f/goat/origin_destination",
        category="geoanalysis",
        docs_path="/toolbox/geoanalysis/origin_destination",
        keywords=("geoanalysis", "od", "origin", "destination", "matrix", "flow"),
    ),
    # Accessibility indicators
    ToolDefinition(
        name="heatmap_gravity",
        display_name="Heatmap Gravity",
        description="Gravity-based spatial accessibility analysis",
        module_path="goatlib.tools.heatmap_gravity",
        params_class_name="HeatmapGravityToolParams",
        windmill_path="f/goat/heatmap_gravity",
        category="accessibility_indicators",
        keywords=(
            "accessibility",
            "heatmap",
            "gravity",
            "opportunities",
            "travel time",
        ),
        docs_path="/toolbox/accessibility_indicators/gravity",
    ),
    ToolDefinition(
        name="heatmap_closest_average",
        display_name="Heatmap Closest Average",
        description="Average distance/time to N closest destinations",
        module_path="goatlib.tools.heatmap_closest_average",
        params_class_name="HeatmapClosestAverageToolParams",
        windmill_path="f/goat/heatmap_closest_average",
        category="accessibility_indicators",
        keywords=(
            "accessibility",
            "heatmap",
            "closest",
            "average",
            "distance",
            "travel time",
        ),
        docs_path="/toolbox/accessibility_indicators/closest_average",
    ),
    ToolDefinition(
        name="heatmap_connectivity",
        display_name="Heatmap Connectivity",
        description="Total area reachable within max travel cost",
        module_path="goatlib.tools.heatmap_connectivity",
        params_class_name="HeatmapConnectivityToolParams",
        windmill_path="f/goat/heatmap_connectivity",
        category="accessibility_indicators",
        keywords=(
            "accessibility",
            "heatmap",
            "connectivity",
            "reachability",
            "travel time",
        ),
        docs_path="/toolbox/accessibility_indicators/connectivity",
    ),
    ToolDefinition(
        name="oev_gueteklassen",
        display_name="ÖV-Güteklassen",
        description="Public transport quality classes based on Swiss ARE methodology",
        module_path="goatlib.tools.oev_gueteklassen",
        params_class_name="OevGueteklassenToolParams",
        windmill_path="f/goat/oev_gueteklassen",
        category="accessibility_indicators",
        keywords=(
            "accessibility",
            "public transport",
            "quality",
            "GTFS",
            "stations",
            "ÖV",
        ),
        docs_path="/toolbox/accessibility_indicators/oev_gueteklassen",
    ),
    ToolDefinition(
        name="layerimport",
        display_name="LayerImport",
        description="Import geospatial data from S3 or WFS into DuckLake",
        module_path="goatlib.tools.layer_import",
        params_class_name="LayerImportParams",
        windmill_path="f/goat/layer_import",
        category="data",
        keywords=("import", "upload", "s3", "wfs", "data"),
        toolbox_hidden=True,
    ),
    ToolDefinition(
        name="layerdelete",
        display_name="LayerDelete",
        description="Delete a layer from DuckLake storage and PostgreSQL metadata",
        module_path="goatlib.tools.layer_delete",
        params_class_name="LayerDeleteParams",
        windmill_path="f/goat/layer_delete",
        category="data",
        keywords=("delete", "remove", "layer", "data"),
        toolbox_hidden=True,
    ),
    ToolDefinition(
        name="layerexport",
        display_name="LayerExport",
        description="Export a layer to file formats (GPKG, GeoJSON, CSV, etc.)",
        module_path="goatlib.tools.layer_export",
        params_class_name="LayerExportParams",
        windmill_path="f/goat/layer_export",
        category="data",
        keywords=("export", "download", "gpkg", "geojson", "data"),
        toolbox_hidden=True,
    ),
)


def get_tool(name: str) -> ToolDefinition | None:
    """Get tool definition by name (case-insensitive)."""
    name_lower = name.lower()
    for tool in TOOL_REGISTRY:
        if tool.name == name_lower:
            return tool
    return None


def get_tools_by_category(category: str) -> list[ToolDefinition]:
    """Get all tools in a category."""
    return [t for t in TOOL_REGISTRY if t.category == category]
