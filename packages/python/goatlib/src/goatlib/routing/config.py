"""
Routing configuration for goatlib.

This module provides default configuration values and limits for routing
operations. Values can be overridden via environment variables.
"""

from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


# =============================================================================
# Mode-Specific Limits
# =============================================================================


class ActiveMobilityLimits(BaseModel):
    """Configuration limits for active mobility routing."""

    max_traveltime: int = Field(
        default=45, description="Maximum travel time in minutes"
    )
    max_distance: int = Field(default=20000, description="Maximum distance in meters")
    max_starting_points: int = Field(
        default=1000, description="Maximum number of starting points"
    )


class MotorizedMobilityLimits(BaseModel):
    """Configuration limits for motorized mobility routing."""

    max_traveltime: int = Field(
        default=90, description="Maximum travel time in minutes"
    )
    max_distance: int = Field(default=100000, description="Maximum distance in meters")
    max_starting_points: int = Field(
        default=1, description="Maximum number of starting points"
    )


class DistanceLimits(BaseModel):
    """Distance-based routing limits."""

    min_distance: int = Field(default=50, description="Minimum distance in meters")
    max_distance: int = Field(default=20000, description="Maximum distance in meters")


class TransitAccessModeLimits(BaseModel):
    """Limits for transit access/egress modes."""

    max_time: int = Field(default=30, description="Maximum time in minutes")
    max_speed: float = Field(default=25.0, description="Maximum speed in km/h")
    default_speed: float = Field(default=5.0, description="Default speed in km/h")


class TransitLimits(BaseModel):
    """Configuration limits for transit routing."""

    max_traveltime: int = Field(
        default=90, description="Maximum total travel time in minutes"
    )
    max_transfers: int = Field(
        default=10, description="Maximum number of transfers allowed"
    )
    max_starting_points: int = Field(
        default=1, description="Maximum number of starting points for PT"
    )

    walk: TransitAccessModeLimits = Field(
        default_factory=lambda: TransitAccessModeLimits(
            max_time=30, max_speed=10.0, default_speed=5.0
        )
    )
    bicycle: TransitAccessModeLimits = Field(
        default_factory=lambda: TransitAccessModeLimits(
            max_time=45, max_speed=30.0, default_speed=15.0
        )
    )


# =============================================================================
# Default Speeds
# =============================================================================


class DefaultSpeeds(BaseModel):
    """Default speeds for different transport modes in km/h."""

    walk: float = Field(default=5.0, description="Walking speed")
    wheelchair: float = Field(default=4.0, description="Wheelchair speed")
    bicycle: float = Field(default=15.0, description="Bicycle speed")
    pedelec: float = Field(default=23.0, description="Pedelec speed")
    car: float = Field(default=50.0, description="Average car speed in urban areas")


# =============================================================================
# Provider-Specific Configuration
# =============================================================================


class R5Config(BaseModel):
    """Configuration for R5 routing provider."""

    default_zoom: int = Field(default=9, description="Default zoom level for R5 grid")
    default_percentiles: list = Field(
        default=[1], description="Default percentiles for R5"
    )
    monte_carlo_draws: int = Field(
        default=200, description="Monte Carlo draws for PT routing"
    )
    worker_version: str = Field(
        default="v7.2", description="R5 worker version identifier"
    )
    variant_index: int = Field(default=-1, description="R5 variant index")


class GoatRoutingConfig(BaseModel):
    """Configuration for GOAT Routing provider (Rust-based)."""

    h3_resolution_walk: int = Field(default=10, description="H3 resolution for walking")
    h3_resolution_bicycle: int = Field(
        default=9, description="H3 resolution for cycling"
    )
    h3_resolution_car: int = Field(default=8, description="H3 resolution for car")


class MotisConfig(BaseModel):
    """Configuration for MOTIS routing provider."""

    default_base_url: str = Field(
        default="https://api.transitous.org", description="Default MOTIS API URL"
    )


# =============================================================================
# Main Settings Class
# =============================================================================


class RoutingSettings(BaseSettings):
    """
    Main routing settings configuration.

    Values can be overridden via environment variables with ROUTING_ prefix.
    For nested values, use double underscores: ROUTING_TRANSIT__MAX_TRANSFERS=5
    """

    # Mode-specific limits
    active_mobility: ActiveMobilityLimits = Field(default_factory=ActiveMobilityLimits)
    motorized_mobility: MotorizedMobilityLimits = Field(
        default_factory=MotorizedMobilityLimits
    )
    distance: DistanceLimits = Field(default_factory=DistanceLimits)
    transit: TransitLimits = Field(default_factory=TransitLimits)

    # Default speeds
    speeds: DefaultSpeeds = Field(default_factory=DefaultSpeeds)

    # Provider configurations
    r5: R5Config = Field(default_factory=R5Config)
    goat_routing: GoatRoutingConfig = Field(default_factory=GoatRoutingConfig)
    motis: MotisConfig = Field(default_factory=MotisConfig)

    model_config = SettingsConfigDict(
        env_prefix="ROUTING_",
        env_nested_delimiter="__",
    )


# =============================================================================
# Singleton Instance
# =============================================================================

# Create a singleton instance for easy import
routing_settings = RoutingSettings()


# =============================================================================
# Helper Functions
# =============================================================================


def get_default_speed(mode: str) -> float:
    """Get the default speed for a transport mode."""
    speeds = routing_settings.speeds
    speed_map = {
        "walk": speeds.walk,
        "walking": speeds.walk,
        "wheelchair": speeds.wheelchair,
        "bicycle": speeds.bicycle,
        "pedelec": speeds.pedelec,
        "car": speeds.car,
    }
    return speed_map.get(mode, speeds.walk)


def get_max_traveltime(mode: str) -> int:
    """Get the maximum travel time for a transport mode category."""
    if mode in ["walk", "walking", "wheelchair", "bicycle", "pedelec"]:
        return routing_settings.active_mobility.max_traveltime
    elif mode == "car":
        return routing_settings.motorized_mobility.max_traveltime
    else:
        return routing_settings.transit.max_traveltime


def get_max_starting_points(mode: str) -> int:
    """Get the maximum number of starting points for a mode category."""
    if mode in ["walk", "walking", "wheelchair", "bicycle", "pedelec"]:
        return routing_settings.active_mobility.max_starting_points
    elif mode == "car":
        return routing_settings.motorized_mobility.max_starting_points
    else:
        return routing_settings.transit.max_starting_points
