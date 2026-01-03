"""
Travel cost schemas for routing in goatlib.

This module provides the travel cost configuration models used for
catchment area and routing computations.
"""

from typing import List, Optional, Union

from pydantic import BaseModel, Field, field_validator, model_validator
from typing_extensions import Self


# =============================================================================
# Active Mobility Travel Cost
# =============================================================================


class TravelTimeCostActiveMobility(BaseModel):
    """Travel time cost configuration for active mobility (walk, bike, etc.)."""

    max_traveltime: int = Field(
        ...,
        title="Max Travel Time",
        description="The maximum travel time in minutes.",
        ge=1,
        le=45,
    )
    steps: int = Field(
        ...,
        title="Steps",
        description="The number of isochrone steps/bands.",
        ge=1,
    )
    speed: float = Field(
        ...,
        title="Speed",
        description="The travel speed in km/h.",
        ge=1,
        le=25,
    )

    @field_validator("steps")
    @classmethod
    def validate_steps(cls, v: int) -> int:
        """Ensure steps don't exceed reasonable limits."""
        if v > 45:
            raise ValueError(
                "The number of steps must not exceed 45 for active mobility."
            )
        return v


class TravelDistanceCostActiveMobility(BaseModel):
    """Travel distance cost configuration for active mobility."""

    max_distance: int = Field(
        ...,
        title="Max Distance",
        description="The maximum distance in meters.",
        ge=50,
        le=20000,
    )
    steps: int = Field(
        ...,
        title="Steps",
        description="The number of isochrone steps/bands.",
        ge=1,
    )

    @field_validator("steps")
    @classmethod
    def validate_steps(cls, v: int) -> int:
        """Ensure steps don't exceed the maximum distance."""
        if v > 20000:
            raise ValueError("The number of steps must not exceed 20000.")
        return v


# =============================================================================
# Motorized Mobility Travel Cost
# =============================================================================


class TravelTimeCostMotorized(BaseModel):
    """Travel time cost configuration for motorized mobility (car, PT)."""

    max_traveltime: int = Field(
        ...,
        title="Max Travel Time",
        description="The maximum travel time in minutes.",
        ge=1,
        le=90,
    )
    steps: int = Field(
        ...,
        title="Steps",
        description="The number of isochrone steps/bands.",
        ge=1,
    )

    @field_validator("steps")
    @classmethod
    def validate_steps(cls, v: int) -> int:
        """Ensure steps don't exceed reasonable limits."""
        if v > 90:
            raise ValueError(
                "The number of steps must not exceed 90 for motorized mobility."
            )
        return v


class TravelDistanceCostMotorized(BaseModel):
    """Travel distance cost configuration for motorized mobility."""

    max_distance: int = Field(
        ...,
        title="Max Distance",
        description="The maximum distance in meters.",
        ge=50,
        le=100000,
    )
    steps: int = Field(
        ...,
        title="Steps",
        description="The number of isochrone steps/bands.",
        ge=1,
    )

    @field_validator("steps")
    @classmethod
    def validate_steps(cls, v: int) -> int:
        """Ensure steps don't exceed reasonable limits."""
        if v > 100000:
            raise ValueError("The number of steps must not exceed 100000.")
        return v


# =============================================================================
# Public Transport Travel Cost (uses cutoffs instead of steps)
# =============================================================================


class TravelTimeCostPT(BaseModel):
    """
    Travel time cost configuration for public transport.

    Uses cutoffs (specific time thresholds) instead of regular steps,
    which is more suitable for PT routing where travel times are discrete.
    """

    max_traveltime: int = Field(
        ...,
        title="Max Travel Time",
        description="The maximum travel time in minutes.",
        ge=1,
        le=90,
    )
    cutoffs: Optional[List[int]] = Field(
        None,
        title="Time Cutoffs",
        description="List of specific travel time cutoffs in minutes. If not provided, uses steps.",
        min_length=1,
    )
    steps: Optional[int] = Field(
        None,
        title="Steps",
        description="Number of evenly-spaced isochrone bands (alternative to cutoffs).",
        ge=1,
    )

    @model_validator(mode="after")
    def validate_cutoffs_or_steps(self) -> Self:
        """Ensure either cutoffs or steps is provided, and validate them."""
        if self.cutoffs is None and self.steps is None:
            raise ValueError("Either 'cutoffs' or 'steps' must be provided.")

        if self.cutoffs is not None:
            # Validate cutoffs
            for cutoff in self.cutoffs:
                if cutoff > self.max_traveltime:
                    raise ValueError(
                        f"Cutoff {cutoff} exceeds maximum travel time {self.max_traveltime}."
                    )
                if cutoff <= 0:
                    raise ValueError("All cutoffs must be positive.")

            # Ensure sorted and unique
            sorted_unique = sorted(set(self.cutoffs))
            if self.cutoffs != sorted_unique:
                self.cutoffs = sorted_unique

        return self

    def get_cutoffs(self) -> List[int]:
        """Get cutoffs list, generating from steps if needed."""
        if self.cutoffs:
            return self.cutoffs
        if self.steps:
            step_size = self.max_traveltime / self.steps
            return [int(step_size * (i + 1)) for i in range(self.steps)]
        return [self.max_traveltime]


# =============================================================================
# Decay Functions (for accessibility analysis)
# =============================================================================


class DecayFunctionType(str):
    """Types of decay functions for accessibility calculations."""

    LOGISTIC = "logistic"
    LINEAR = "linear"
    EXPONENTIAL = "exponential"
    STEP = "step"


class DecayFunction(BaseModel):
    """Decay function configuration for accessibility calculations."""

    type: str = Field(
        default="logistic",
        description="Type of decay function: logistic, linear, exponential, or step.",
    )
    standard_deviation_minutes: Optional[int] = Field(
        default=12,
        description="Standard deviation in minutes (for logistic decay).",
    )
    width_minutes: Optional[int] = Field(
        default=10,
        description="Width in minutes (for logistic decay).",
    )


# =============================================================================
# Unified Travel Cost Type
# =============================================================================

# Type alias for any travel cost configuration
TravelCostActiveMobility = Union[
    TravelTimeCostActiveMobility, TravelDistanceCostActiveMobility
]
TravelCostMotorized = Union[TravelTimeCostMotorized, TravelDistanceCostMotorized]
TravelCostPT = TravelTimeCostPT
TravelCost = Union[
    TravelTimeCostActiveMobility,
    TravelDistanceCostActiveMobility,
    TravelTimeCostMotorized,
    TravelDistanceCostMotorized,
    TravelTimeCostPT,
]
