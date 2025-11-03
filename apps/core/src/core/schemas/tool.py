from enum import Enum
from typing import Any, Dict, List
from uuid import UUID

from pydantic import BaseModel, Field, ValidationInfo, field_validator, model_validator
from typing_extensions import Self

from core.db.models.layer import LayerType, ToolType
from core.schemas.catchment_area import (
    ICatchmentAreaActiveMobility,
    ICatchmentAreaCar,
    ICatchmentAreaPT,
)
from core.schemas.colors import ColorRangeType
from core.schemas.layer import FeatureGeometryType
from core.schemas.oev_gueteklasse import IOevGueteklasse
from core.schemas.toolbox_base import (
    ColumnStatistic,
    ColumnStatisticsOperation,
    DefaultResultLayerName,
    InputLayerType,
    input_layer_table,
    input_layer_type_feature_all,
    input_layer_type_point,
    input_layer_type_point_polygon,
    input_layer_type_polygon,
)


class IJoin(BaseModel):
    """Join tool schema."""

    target_layer_project_id: int = Field(
        ...,
        title="Target Layer Project ID",
        description="The ID of the layer project the data will be joined.",
    )
    target_field: str = Field(
        ...,
        title="Target Field",
        description="The field in the target layer that is used for the join.",
    )
    join_layer_project_id: int = Field(
        ...,
        title="Join Layer ID",
        description="The ID of the layer project that contains the joined data.",
    )
    join_field: str = Field(
        ...,
        title="Join Field",
        description="The field in the join layer that is used for the join.",
    )
    column_statistics: ColumnStatistic = Field(
        ...,
        title="Column Statistics",
        description="The column statistics to be calculated.",
    )

    @property
    def input_layer_types(self) -> Dict[str, InputLayerType]:
        return {
            "target_layer_project_id": InputLayerType(
                layer_types=[LayerType.feature, LayerType.table],
                feature_layer_geometry_types=[
                    FeatureGeometryType.point,
                    FeatureGeometryType.polygon,
                    FeatureGeometryType.line,
                ],
            ),
            "join_layer_project_id": InputLayerType(
                layer_types=[LayerType.feature, LayerType.table],
                feature_layer_geometry_types=[
                    FeatureGeometryType.point,
                    FeatureGeometryType.polygon,
                    FeatureGeometryType.line,
                ],
            ),
        }

    @property
    def tool_type(self) -> ToolType:
        return ToolType.join

    @property
    def properties_base(self) -> Dict[str, Any]:
        return {
            DefaultResultLayerName.join: {
                "color_range_type": ColorRangeType.sequential,
                "color_field": {
                    "name": self.column_statistics.operation.value,
                    "type": "number",
                },
                "color_scale": "quantile",
            }
        }


class AreaLayerType(str, Enum):
    """Area layer type schema."""

    feature = "feature"
    h3_grid = "h3_grid"


class IAggregationBase(BaseModel):
    source_layer_project_id: int = Field(
        ...,
        title="Point Layer ID",
        description="The ID of the layer that contains the feature to be aggregated.",
    )
    area_type: AreaLayerType = Field(
        ...,
        title="Area Type",
        description="The type of the layer that contains the areas that are used to aggregate the source layer. It can be a feature layer or a H3 grid.",
    )
    aggregation_layer_project_id: int | None = Field(
        None,
        title="Area Layer ID",
        description="The ID of the layer that contains the areas that are used to aggregate the source layer.",
    )
    h3_resolution: int | None = Field(
        None,
        title="H3 Resolution",
        description="The resolution of the H3 grid that is used to aggregate the points.",
        ge=3,
        le=10,
    )
    column_statistics: ColumnStatistic = Field(
        ...,
        title="Column Statistics",
        description="The column statistics to be calculated.",
    )
    source_group_by_field: list[str] | None = Field(
        None,
        title="Source Group By Field",
        description="The field in the source layer that is used to group the aggregated points.",
    )
    scenario_id: UUID | None = Field(
        None,
        title="Scenario ID",
        description="The ID of the scenario that is to be applied on the input layer or base network.",
    )

    @field_validator("source_group_by_field", mode="after")
    @classmethod
    def check_source_group_by_field(
        cls: type["IAggregationBase"], value: List[str] | None
    ) -> List[str] | None:
        if value is not None and not (0 <= len(value) <= 3):
            raise ValueError(
                "The source_group_by_field must have between 0 and 3 elements."
            )
        return value

    @field_validator("h3_resolution", mode="after", check_fields=True)
    @classmethod
    def h3_grid_requires_resolution(
        cls: type["IAggregationBase"], value: int | None, info: ValidationInfo
    ) -> int | None:
        if info.data.get("area_type") == AreaLayerType.h3_grid and value is None:
            raise ValueError(
                "If area_type is h3_grid then h3_resolution cannot be null."
            )
        return value

    @field_validator("aggregation_layer_project_id", mode="after", check_fields=True)
    @classmethod
    def feature_layer_requires_aggregation_layer_project_id(
        cls: type["IAggregationBase"], value: int | None, info: ValidationInfo
    ) -> int | None:
        if info.data.get("area_type") == AreaLayerType.feature and value is None:
            raise ValueError(
                "If area_type is feature then aggregation_layer_project_id cannot be null."
            )
        return value

    @model_validator(mode="after")
    def no_conflicting_area_layer_and_resolution(self) -> Self:
        if self.aggregation_layer_project_id and self.h3_resolution:
            raise ValueError(
                "Cannot specify both aggregation_layer_project_id and h3_resolution at the same time."
            )
        return self

    @field_validator("column_statistics", mode="after", check_fields=True)
    @classmethod
    def check_column_statistics(
        cls: type["IAggregationBase"], value: ColumnStatistic
    ) -> ColumnStatistic:
        if value.operation == ColumnStatisticsOperation.count:
            if value.field is not None:
                raise ValueError("Field is not allowed for count operation.")
        else:
            if value.field is None:
                raise ValueError("Field is required for all operations except count.")
        return value


class IAggregationPoint(IAggregationBase):
    """Aggregation tool schema."""

    @property
    def input_layer_types(self) -> Dict[str, InputLayerType]:
        if self.area_type == AreaLayerType.feature:
            return {
                "source_layer_project_id": input_layer_type_point,
                "aggregation_layer_project_id": input_layer_type_polygon,
            }
        elif self.area_type == AreaLayerType.h3_grid:
            return {"source_layer_project_id": input_layer_type_point}

    @property
    def tool_type(self) -> ToolType:
        return ToolType.aggregate_point

    @property
    def properties_base(self) -> Dict[str, Any]:
        return {
            DefaultResultLayerName.aggregate_point: {
                "color_range_type": ColorRangeType.sequential,
                "color_field": {
                    "name": self.column_statistics.operation.value,
                    "type": "number",
                },
                "color_scale": "quantile",
            }
        }


class IAggregationPolygon(IAggregationBase):
    weigthed_by_intersecting_area: bool | None = Field(
        False,
        title="Weighted By Intersection Area",
        description="If true, the aggregated values are weighted by the share of the intersection area between the source layer and the aggregation layer.",
    )

    @property
    def input_layer_types(self) -> Dict[str, InputLayerType]:
        if self.area_type == AreaLayerType.feature:
            return {
                "source_layer_project_id": input_layer_type_polygon,
                "aggregation_layer_project_id": input_layer_type_polygon,
            }
        elif self.area_type == AreaLayerType.h3_grid:
            return {"source_layer_project_id": input_layer_type_polygon}

    @property
    def tool_type(self) -> ToolType:
        return ToolType.aggregate_polygon

    @property
    def properties_base(self) -> Dict[str, Any]:
        return {
            DefaultResultLayerName.aggregate_polygon: {
                "color_range_type": ColorRangeType.sequential,
                "color_field": {
                    "name": self.column_statistics.operation.value,
                    "type": "number",
                },
                "color_scale": "quantile",
            }
        }


class IBuffer(BaseModel):
    """Buffer tool schema."""

    source_layer_project_id: int = Field(
        ...,
        title="Source Layer Project ID",
        description="The ID of the layer project that conains the geometries that should be buffered.",
    )
    max_distance: int = Field(
        ...,
        title="Max Distance",
        description="The maximum distance in meters.",
        ge=1,
        le=5000000,
    )
    distance_step: int = Field(
        ...,
        title="Distance Step",
        description="The number of steps.",
        ge=1,
        le=20,
    )
    polygon_union: bool | None = Field(
        None,
        title="Polygon Union",
        description="If true, the polygons returned will be the geometrical union of buffers with the same step.",
    )
    polygon_difference: bool | None = Field(
        None,
        title="Polygon Difference",
        description="If true, the polygons returned will be the geometrical difference of the current step and the predecessor steps.",
    )
    scenario_id: UUID | None = Field(
        None,
        title="Scenario ID",
        description="The ID of the scenario that is to be applied on the input layer or base network.",
    )

    # Make sure that the number of steps is smaller then then max distance
    @field_validator("distance_step", mode="after", check_fields=True)
    @classmethod
    def distance_step_smaller_than_max_distance(
        cls: type["IBuffer"], value: int, info: ValidationInfo
    ) -> int:
        if value > info.data["max_distance"]:
            raise ValueError("The distance step must be smaller than the max distance.")
        return value

    # Make sure that polygon difference is only True if polygon union is True
    @field_validator("polygon_difference", mode="after")
    @classmethod
    def check_polygon_difference(
        cls: type["IBuffer"], value: bool | None, info: ValidationInfo
    ) -> bool | None:
        if info.data["polygon_union"] is False and value is True:
            raise ValueError(
                "You can only have polygon difference if polygon union is True."
            )
        return value

    @property
    def input_layer_types(self) -> Dict[str, InputLayerType]:
        return {"source_layer_project_id": input_layer_type_feature_all}

    @property
    def tool_type(self) -> ToolType:
        return ToolType.buffer

    @property
    def properties_base(self) -> Dict[str, Any]:
        breaks = (
            self.max_distance / self.distance_step
            if self.max_distance / self.distance_step < 7
            else 7
        )
        return {
            DefaultResultLayerName.buffer: {
                "color_range_type": ColorRangeType.sequential,
                "color_field": {"name": "radius_size", "type": "number"},
                "color_scale": "quantile",
                "breaks": breaks,
            }
        }


class IOriginDestination(BaseModel):
    """Origin Destination tool schema."""

    geometry_layer_project_id: int = Field(
        ...,
        title="Geometry layer Project ID",
        description="The ID of the layer project that conains the origins and destinations geometries.",
    )
    origin_destination_matrix_layer_project_id: int = Field(
        ...,
        title="Origins Destinations Matrix Layer Project ID",
        description="The ID of the layer project that conains the origins and destinations matrix.",
    )
    unique_id_column: str = Field(
        ...,
        title="Unique ID Column",
        description="The column that contains the unique IDs in geometry layer.",
    )
    origin_column: str = Field(
        ...,
        title="Origin Column",
        description="The column that contains the origins in the origin destination matrix.",
    )
    destination_column: str = Field(
        ...,
        title="Destination Column",
        description="The column that contains the destinations in the origin destination matrix.",
    )
    weight_column: str = Field(
        ...,
        title="Weight Column",
        description="The column that contains the weights in the origin destination matrix.",
    )

    @property
    def input_layer_types(self) -> Dict[str, InputLayerType]:
        return {
            "geometry_layer_project_id": input_layer_type_point_polygon,
            "origin_destination_matrix_layer_project_id": input_layer_table,
        }

    @property
    def tool_type(self) -> ToolType:
        return ToolType.origin_destination

    @property
    def properties_base(self) -> Dict[str, Any]:
        return {
            DefaultResultLayerName.origin_destination_point: {
                "color_range_type": ColorRangeType.sequential,
                "color_field": {"name": self.weight_column, "type": "number"},
                "color_scale": "quantile",
            },
            DefaultResultLayerName.origin_destination_relation: {
                "color_range_type": ColorRangeType.sequential,
                "color_field": {"name": self.weight_column, "type": "number"},
                "color_scale": "quantile",
            },
        }


class IToolParam(BaseModel):
    data: object

    @field_validator("data", mode="after")
    @classmethod
    def check_type(
        cls: type["IToolParam"], value: object
    ) -> (
        IJoin
        | IAggregationPoint
        | ICatchmentAreaActiveMobility
        | IOevGueteklasse
        | ICatchmentAreaCar
        | ICatchmentAreaPT
    ):
        allowed_types = (
            IJoin,
            IAggregationPoint,
            ICatchmentAreaActiveMobility,
            IOevGueteklasse,
            ICatchmentAreaCar,
            ICatchmentAreaPT,
        )
        if not isinstance(value, allowed_types):
            raise ValueError(f"Input type {type(value).__name__} not allowed")
        return value


request_examples_join = {
    "join_count": {
        "summary": "Join Count",
        "value": {
            "target_layer_project_id": 1,
            "target_field": "target_field_example",
            "join_layer_project_id": 2,
            "join_field": "join_field_example",
            "column_statistics": {
                "operation": ColumnStatisticsOperation.count.value,
                "field": "field_example1",
            },
        },
    },
    "join_sum": {
        "summary": "Join Sum",
        "value": {
            "target_layer_project_id": 1,
            "target_field": "target_field_example2",
            "join_layer_project_id": 2,
            "join_field": "join_field_example2",
            "column_statistics": {
                "operation": ColumnStatisticsOperation.sum.value,
                "field": "field_example2",
            },
        },
    },
}

request_examples_aggregation_point = {
    "aggregation_feature_layer": {
        "summary": "Aggregation Feature Layer",
        "value": {
            "source_layer_project_id": 1,
            "area_type": AreaLayerType.feature.value,
            "aggregation_layer_project_id": 2,
            "column_statistics": {"operation": "sum", "field": "field_example1"},
            "source_group_by_field": ["group_by_example1"],
        },
    },
    "aggregation_h3_grid": {
        "summary": "Aggregation H3 Grid",
        "value": {
            "source_layer_project_id": 1,
            "area_type": AreaLayerType.h3_grid.value,
            "h3_resolution": 6,
            "column_statistics": {"operation": "sum", "field": "field_example2"},
            "source_group_by_field": ["group_by_example2"],
        },
    },
}

request_examples_aggregation_polygon = {
    "aggregation_polygon_feature_layer": {
        "summary": "Aggregation Polygon Feature Layer",
        "value": {
            "source_layer_project_id": 1,
            "area_type": AreaLayerType.feature.value,
            "aggregation_layer_project_id": 2,
            "weigthed_by_intersecting_area": True,
            "column_statistics": {"operation": "sum", "field": "field_example1"},
            "source_group_by_field": ["group_by_example1"],
        },
    },
    "aggregation_polygon_h3_grid": {
        "summary": "Aggregation Polygon H3 Grid",
        "value": {
            "source_layer_project_id": 1,
            "area_type": AreaLayerType.h3_grid.value,
            "h3_resolution": 6,
            "weigthed_by_intersecting_area": False,
            "column_statistics": {"operation": "sum", "field": "field_example2"},
            "source_group_by_field": ["group_by_example2"],
        },
    },
}

request_example_buffer = {
    "buffer_union": {
        "summary": "Buffer union polygons",
        "value": {
            "source_layer_project_id": 1,
            "max_distance": 1000,
            "distance_step": 100,
            "polygon_union": True,
            "polygon_difference": False,
        },
    },
    "buffer_union_difference": {
        "summary": "Buffer union and difference polygons",
        "value": {
            "source_layer_project_id": 1,
            "max_distance": 1000,
            "distance_step": 100,
            "polygon_union": True,
            "polygon_difference": True,
        },
    },
}
