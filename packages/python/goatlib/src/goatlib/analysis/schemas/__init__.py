# Analysis schemas

# Keep vector as alias for backwards compatibility
from . import (
    data_management,
    geocoding,
    geoprocessing,
    heatmap,
    oev_gueteklasse,
    statistics,
    trip_count,
    ui,
    vector,
)
from .base import ALL_GEOMETRY_TYPES, POLYGON_TYPES, GeometryType
from .catchment_area import (
    AccessEgressMode,
    CatchmentAreaRoutingMode,
    CatchmentAreaToolParams,
    CatchmentAreaType,
    PTMode,
    PTTimeWindow,
)
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
from .geocoding import (
    FieldSourceType,
    GeocodingInputMode,
    GeocodingParams,
    GeocodingResult,
    SECTION_GEOCODING,
)
from .heatmap import (
    HeatmapClosestAverageParams,
    HeatmapConnectivityParams,
    HeatmapGravityParams,
    HeatmapRoutingMode,
    ImpedanceFunction,
    OpportunityClosestAverage,
    OpportunityGravity,
    RoutingMode,
)
from .oev_gueteklasse import (
    CatchmentType as OevCatchmentType,
    OevGueteklasseParams,
    OevGueteklasseStationConfig,
    PTTimeWindow as OevPTTimeWindow,
    STATION_CONFIG_DEFAULT,
)
from .trip_count import TripCountStationParams
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
from .ui import (
    SECTION_AREA,
    SECTION_CONFIGURATION,
    SECTION_INPUT,
    SECTION_INPUT_AGGREGATE,
    SECTION_OPPORTUNITIES,
    SECTION_OPTIONS,
    SECTION_OUTPUT,
    SECTION_ROUTING,
    SECTION_SCENARIO,
    SECTION_STATISTICS,
    SECTION_TIME,
    UIFieldConfig,
    UISection,
    layer_selector_field,
    merge_ui_field,
    scenario_selector_field,
    ui_field,
    ui_sections,
)

__all__ = [
    # Modules
    "vector",  # Backwards compatibility alias
    "geoprocessing",
    "geocoding",
    "data_management",
    "statistics",
    "heatmap",
    "ui",
    # Base schemas
    "GeometryType",
    "ALL_GEOMETRY_TYPES",
    "POLYGON_TYPES",
    # UI schemas
    "UISection",
    "UIFieldConfig",
    "ui_field",
    "ui_sections",
    "merge_ui_field",
    "layer_selector_field",
    "scenario_selector_field",
    "SECTION_ROUTING",
    "SECTION_CONFIGURATION",
    "SECTION_INPUT",
    "SECTION_INPUT_AGGREGATE",
    "SECTION_OUTPUT",
    "SECTION_OPTIONS",
    "SECTION_OPPORTUNITIES",
    "SECTION_SCENARIO",
    "SECTION_STATISTICS",
    "SECTION_TIME",
    "SECTION_AREA",
    # Geocoding schemas
    "GeocodingParams",
    "FieldSourceType",
    "GeocodingInputMode",
    "GeocodingResult",
    "SECTION_GEOCODING",
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
    # Catchment Area schemas
    "PTMode",
    "AccessEgressMode",
    "CatchmentAreaType",
    "CatchmentAreaRoutingMode",
    "CatchmentAreaToolParams",
    "PTTimeWindow",
    # ÖV-Güteklassen schemas
    "oev_gueteklasse",
    "OevGueteklasseParams",
    "OevGueteklasseStationConfig",
    "OevPTTimeWindow",
    "OevCatchmentType",
    "STATION_CONFIG_DEFAULT",
    # Trip Count schemas
    "trip_count",
    "TripCountStationParams",
]
