import logging
from enum import StrEnum
from typing import Self

from pydantic import BaseModel, Field, model_validator

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
    # Prefer routing_mode; support legacy aliases
    routing_mode: RoutingMode = Field(
        description="Transport mode selecting the traveltime matrix.",
    )
    od_matrix_source: str = Field(
        ...,
        description=(
            "Path, directory, glob pattern, or S3 URI to OD travel time matrix Parquet file(s). "
            "Needs columns: orig_id, dest_id, traveltime. "
            "Supports local files, directories, globs, and S3 paths."
        ),
    )
    output_path: str = Field(..., description="Output GeoParquet path.")


class OpportunityBase(BaseModel):
    input_path: str = Field(..., description="Path to opportunity dataset.")
    name: str | None = Field(
        None,
        description=(
            "Optional name for the opportunity dataset; "
            "if not set, the filename without extension is used."
        ),
    )
    max_traveltime: int = Field(..., ge=1, le=60, description="Minutes.")


class OpportunityGravity(OpportunityBase):
    sensitivity: float = Field(..., gt=0.0)
    potential_field: str | None = Field(
        None, description="Field name to use as potential."
    )
    potential_constant: float | None = Field(
        None, gt=0.0, description="Constant potential; overrides field if set."
    )
    potential_expression: str | None = Field(
        None,
        description=(
            "Expression to compute potential for polygons, e.g. 'area', 'perimeter', or a custom formula. "
            "Overrides potential_field and potential_constant if set."
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
    impedance: ImpedanceFunction
    max_sensitivity: float = Field(
        10.0, gt=0.0, description="Max sensitivity used for normalization."
    )
    opportunities: list[OpportunityGravity]
