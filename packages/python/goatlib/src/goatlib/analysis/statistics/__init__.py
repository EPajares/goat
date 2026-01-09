"""Statistics analysis tools for vector data.

This module provides functions for calculating various statistics on DuckDB tables:
- Feature count: Count features with optional filtering
- Unique values: Get unique values with occurrence counts
- Class breaks: Calculate classification breaks using various methods
- Area statistics: Calculate area-based statistics for polygon features
- Extent: Calculate bounding box extent with optional filtering
"""

from goatlib.analysis.schemas.statistics import (
    AreaOperation,
    AreaStatisticsInput,
    AreaStatisticsResult,
    ClassBreakMethod,
    ClassBreaksInput,
    ClassBreaksResult,
    ExtentInput,
    ExtentResult,
    FeatureCountInput,
    FeatureCountResult,
    SortOrder,
    UniqueValue,
    UniqueValuesInput,
    UniqueValuesResult,
)
from goatlib.analysis.statistics.area_statistics import calculate_area_statistics
from goatlib.analysis.statistics.class_breaks import calculate_class_breaks
from goatlib.analysis.statistics.extent import calculate_extent
from goatlib.analysis.statistics.feature_count import calculate_feature_count
from goatlib.analysis.statistics.unique_values import calculate_unique_values

__all__ = [
    # Functions
    "calculate_feature_count",
    "calculate_unique_values",
    "calculate_class_breaks",
    "calculate_area_statistics",
    "calculate_extent",
    # Schemas - Enums
    "ClassBreakMethod",
    "SortOrder",
    "AreaOperation",
    # Schemas - Inputs
    "FeatureCountInput",
    "AreaStatisticsInput",
    "UniqueValuesInput",
    "ClassBreaksInput",
    "ExtentInput",
    # Schemas - Results
    "FeatureCountResult",
    "UniqueValue",
    "UniqueValuesResult",
    "ClassBreaksResult",
    "AreaStatisticsResult",
    "ExtentResult",
]
