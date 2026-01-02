import logging
from enum import StrEnum
from typing import Self

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from goatlib.analysis.schemas.ui import (
    SECTION_CONFIGURATION,
    SECTION_OPPORTUNITIES,
    SECTION_ROUTING,
    ui_field,
    ui_sections,
)

logger = logging.getLogger(__name__)


class RoutingMode(StrEnum):
    walking = "walking"
    bicycle = "bicycle"
    pedelec = "pedelec"
    public_transport = "public_transport"
    car = "car"


class ImpedanceFunction(StrEnum):
    gaussian = "gaussian"
    linear = "linear"
    exponential = "exponential"
    power = "power"


class HeatmapCommon(BaseModel):
    """Base parameters shared by all heatmap analysis types."""

    model_config = ConfigDict(
        json_schema_extra=ui_sections(
            SECTION_ROUTING,
            SECTION_CONFIGURATION,
            SECTION_OPPORTUNITIES,
        )
    )

    # Prefer routing_mode; support legacy aliases
    routing_mode: RoutingMode = Field(
        description="Transport mode selecting the OD matrix.",
        json_schema_extra=ui_field(
            section="routing",
            field_order=1,
        ),
    )
    od_matrix_path: str = Field(
        ...,
        description=(
            "Path, directory, glob pattern, or S3 URI to OD matrix Parquet file(s). "
            "Needs columns: orig_id, dest_id, cost. "
            "Supports local files, directories, globs, and S3 paths."
        ),
        json_schema_extra=ui_field(
            section="configuration",
            field_order=1,
            hidden=True,  # Internal field, typically derived from routing_mode
        ),
    )
    od_column_map: dict[str, str] = Field(
        default_factory=lambda: {
            "orig_id": "orig_id",
            "dest_id": "dest_id",
            "cost": "cost",
        },
        description=(
            "Column mapping for the OD matrix. "
            "Keys are the expected standard names: 'orig_id', 'dest_id', 'cost'. "
            "Values are the actual column names in the user-provided dataset."
        ),
        examples=[{"orig_id": "from_zone", "dest_id": "to_zone", "cost": "time_min"}],
        json_schema_extra=ui_field(
            section="configuration",
            field_order=2,
            hidden=True,  # Advanced setting, rarely changed
        ),
    )

    @field_validator("od_column_map")
    @classmethod
    def validate_od_column_map(cls: Self, v: dict[str, str]) -> dict[str, str]:
        required_keys = {"orig_id", "dest_id", "cost"}
        missing = required_keys - v.keys()
        if missing:
            raise ValueError(f"Missing required mapping keys: {missing}")
        return v

    output_path: str = Field(
        ...,
        description="Output GeoParquet path.",
        json_schema_extra=ui_field(
            section="configuration",
            field_order=99,
            hidden=True,  # Internal field
        ),
    )


class OpportunityBase(BaseModel):
    """Base parameters for opportunity datasets."""

    input_path: str = Field(
        ...,
        description="Path to opportunity dataset.",
        json_schema_extra=ui_field(
            section="opportunities",
            field_order=1,
            widget="layer-selector",
        ),
    )
    name: str | None = Field(
        None,
        description=(
            "Optional name for the opportunity dataset; "
            "if not set, the filename without extension is used."
        ),
        json_schema_extra=ui_field(
            section="opportunities",
            field_order=2,
        ),
    )
    max_cost: int = Field(
        ...,
        ge=1,
        le=60,
        description="Max cost.",
        json_schema_extra=ui_field(
            section="opportunities",
            field_order=3,
            label_key="max_cost",
        ),
    )


class OpportunityGravity(OpportunityBase):
    """Opportunity dataset parameters for gravity-based heatmaps."""

    sensitivity: float = Field(
        ...,
        gt=0.0,
        json_schema_extra=ui_field(
            section="opportunities",
            field_order=10,
        ),
    )
    potential_field: str | None = Field(
        None,
        description="Field name to use as potential.",
        json_schema_extra=ui_field(
            section="opportunities",
            field_order=5,
            mutually_exclusive_group="potential_source",
            priority=1,  # Default option (lowest priority number)
        ),
    )
    potential_constant: float | None = Field(
        None,
        gt=0.0,
        description="Constant potential; overrides field if set.",
        json_schema_extra=ui_field(
            section="opportunities",
            field_order=6,
            mutually_exclusive_group="potential_source",
            priority=2,
        ),
    )
    potential_expression: str | None = Field(
        None,
        description=(
            "Expression to compute potential for polygons, e.g. 'area', 'perimeter', or a custom formula. "
            "Overrides potential_field and potential_constant if set."
        ),
        json_schema_extra=ui_field(
            section="opportunities",
            field_order=7,
            mutually_exclusive_group="potential_source",
            priority=3,
        ),
    )

    @model_validator(mode="after")
    def validate_potential_fields(self: Self) -> Self:
        set_fields = [
            f
            for f in ["potential_expression", "potential_constant", "potential_field"]
            if getattr(self, f) is not None
        ]
        if not set_fields:
            raise ValueError(
                "One of potential_expression, potential_constant, or potential_field must be set."
            )
        if len(set_fields) > 1:
            precedence = {
                "potential_expression": 1,
                "potential_constant": 2,
                "potential_field": 3,
            }
            chosen = min(set_fields, key=lambda f: precedence[f])
            logger.warning(
                f"Multiple potential fields set ({set_fields}); "
                f"using '{chosen}' due to precedence: "
                "potential_expression > potential_constant > potential_field."
            )
        return self


class HeatmapGravityParams(HeatmapCommon):
    """Parameters for gravity-based accessibility heatmaps."""

    impedance: ImpedanceFunction = Field(
        ...,
        json_schema_extra=ui_field(
            section="configuration",
            field_order=1,
        ),
    )
    max_sensitivity: float = Field(
        300000,
        gt=0.0,
        description="Max sensitivity used for normalization.",
        json_schema_extra=ui_field(
            section="configuration",
            field_order=2,
        ),
    )
    opportunities: list[OpportunityGravity] = Field(
        ...,
        json_schema_extra=ui_field(
            section="opportunities",
            repeatable=True,
            min_items=1,
        ),
    )


class OpportunityClosestAverage(OpportunityBase):
    """Opportunity dataset parameters for closest-average heatmaps."""

    n_destinations: int = Field(
        ...,
        ge=1,
        description="Number of closest destinations to average",
        json_schema_extra=ui_field(
            section="opportunities",
            field_order=5,
        ),
    )


class HeatmapClosestAverageParams(HeatmapCommon):
    """Parameters for closest-average accessibility heatmaps."""

    opportunities: list[OpportunityClosestAverage] = Field(
        ...,
        json_schema_extra=ui_field(
            section="opportunities",
            repeatable=True,
            min_items=1,
        ),
    )


class HeatmapConnectivityParams(HeatmapCommon):
    """Parameters for connectivity-based heatmaps."""

    reference_area_path: str = Field(
        ...,
        description="Path to reference area dataset (polygons/points/lines)",
        json_schema_extra=ui_field(
            section="configuration",
            field_order=3,
            widget="layer-selector",
            widget_options={
                "geometry_types": ["Polygon", "MultiPolygon", "Point", "LineString"]
            },
        ),
    )
    max_cost: int = Field(
        ...,
        description="Max cost. It can be time, distance or any other cost unit.",
        json_schema_extra=ui_field(
            section="configuration",
            field_order=4,
        ),
    )
