# Analysis schemas

# Keep vector as alias for backwards compatibility
from . import data_management, geoprocessing, heatmap, statistics, vector
from .base import ALL_GEOMETRY_TYPES, POLYGON_TYPES, GeometryType
from .data_management import (
    AttributeRelationship,
    FieldStatistic,
    JoinOperationType,
    JoinParams,
    JoinType,
    MergeParams,
    MultipleMatchingRecordsType,
    SortConfiguration,
    SpatialRelationshipType,
    StatisticOperation,
)
from .data_management import (
    SortOrder as JoinSortOrder,
)
from .geoprocessing import (
    BufferParams,
    CentroidParams,
    ClipParams,
    DifferenceParams,
    IntersectionParams,
    OriginDestinationParams,
    UnionParams,
)
from .heatmap import (
    HeatmapClosestAverageParams,
    HeatmapConnectivityParams,
    HeatmapGravityParams,
    ImpedanceFunction,
    OpportunityClosestAverage,
    OpportunityGravity,
    RoutingMode,
)
from .statistics import (
    AreaOperation,
    AreaStatisticsInput,
    AreaStatisticsResult,
    ClassBreakMethod,
    ClassBreaksInput,
    ClassBreaksResult,
    FeatureCountInput,
    FeatureCountResult,
    SortOrder,
    UniqueValue,
    UniqueValuesInput,
    UniqueValuesResult,
)

__all__ = [
    # Modules
    "vector",  # Backwards compatibility alias
    "geoprocessing",
    "data_management",
    "statistics",
    "heatmap",
    # Base schemas
    "GeometryType",
    "ALL_GEOMETRY_TYPES",
    "POLYGON_TYPES",
    # Geoprocessing schemas
    "BufferParams",
    "ClipParams",
    "IntersectionParams",
    "UnionParams",
    "DifferenceParams",
    "CentroidParams",
    "OriginDestinationParams",
    # Data management schemas
    "JoinParams",
    "MergeParams",
    "SpatialRelationshipType",
    "JoinOperationType",
    "MultipleMatchingRecordsType",
    "JoinType",
    "JoinSortOrder",
    "StatisticOperation",
    "AttributeRelationship",
    "SortConfiguration",
    "FieldStatistic",
    # Heatmap/Accessibility schemas
    "HeatmapGravityParams",
    "HeatmapConnectivityParams",
    "HeatmapClosestAverageParams",
    "OpportunityGravity",
    "OpportunityClosestAverage",
    "ImpedanceFunction",
    "RoutingMode",
    # Statistics schemas
    "ClassBreakMethod",
    "SortOrder",
    "AreaOperation",
    "FeatureCountInput",
    "AreaStatisticsInput",
    "UniqueValuesInput",
    "ClassBreaksInput",
    "FeatureCountResult",
    "UniqueValue",
    "UniqueValuesResult",
    "ClassBreaksResult",
    "AreaStatisticsResult",
]
