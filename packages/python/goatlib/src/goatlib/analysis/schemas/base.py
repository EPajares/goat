"""Base schemas for analysis operations."""

from enum import StrEnum
from typing import List


class GeometryType(StrEnum):
    """Supported geometry types in DuckDB Spatial"""

    point = "POINT"
    multipoint = "MULTIPOINT"
    linestring = "LINESTRING"
    multilinestring = "MULTILINESTRING"
    polygon = "POLYGON"
    multipolygon = "MULTIPOLYGON"


# Common geometry type groups
ALL_GEOMETRY_TYPES: List[GeometryType] = [
    GeometryType.polygon,
    GeometryType.multipolygon,
    GeometryType.linestring,
    GeometryType.multilinestring,
    GeometryType.point,
    GeometryType.multipoint,
]

POLYGON_TYPES: List[GeometryType] = [
    GeometryType.polygon,
    GeometryType.multipolygon,
]
