from enum import StrEnum
from typing import List

from goatlib.routing.schemas.base import Mode


class MotisMode(StrEnum):
    """MOTIS transport modes enum."""

    WALK = "WALK"
    BIKE = "BIKE"
    RENTAL = "RENTAL"
    CAR = "CAR"
    CAR_PARKING = "CAR_PARKING"
    CAR_DROPOFF = "CAR_DROPOFF"
    ODM = "ODM"
    FLEX = "FLEX"
    TRANSIT = "TRANSIT"
    TRAM = "TRAM"
    SUBWAY = "SUBWAY"
    FERRY = "FERRY"
    AIRPLANE = "AIRPLANE"
    METRO = "METRO"
    BUS = "BUS"
    COACH = "COACH"
    RAIL = "RAIL"
    HIGHSPEED_RAIL = "HIGHSPEED_RAIL"
    LONG_DISTANCE = "LONG_DISTANCE"
    NIGHT_RAIL = "NIGHT_RAIL"
    REGIONAL_FAST_RAIL = "REGIONAL_FAST_RAIL"
    REGIONAL_RAIL = "REGIONAL_RAIL"
    SUBURBAN = "SUBURBAN"  # S-Bahn/suburban rail
    CABLE_CAR = "CABLE_CAR"
    FUNICULAR = "FUNICULAR"
    AREAL_LIFT = "AREAL_LIFT"
    OTHER = "OTHER"


# Mode mappings between MOTIS and internal representations
MOTIS_TO_INTERNAL_MODE_MAP = {
    # Active mobility
    MotisMode.WALK: Mode.WALK,
    MotisMode.BIKE: Mode.BIKE,
    # Public transport - Direct mappings
    MotisMode.BUS: Mode.BUS,
    MotisMode.COACH: Mode.BUS,  # Coach is a type of bus
    MotisMode.TRAM: Mode.TRAM,
    MotisMode.SUBWAY: Mode.SUBWAY,
    MotisMode.METRO: Mode.SUBWAY,  # Metro is subway
    MotisMode.FERRY: Mode.FERRY,
    MotisMode.CABLE_CAR: Mode.CABLE_CAR,
    MotisMode.FUNICULAR: Mode.FUNICULAR,
    # Rail variants - All map to RAIL
    MotisMode.RAIL: Mode.RAIL,
    MotisMode.HIGHSPEED_RAIL: Mode.RAIL,
    MotisMode.LONG_DISTANCE: Mode.RAIL,
    MotisMode.NIGHT_RAIL: Mode.RAIL,
    MotisMode.REGIONAL_FAST_RAIL: Mode.RAIL,
    MotisMode.REGIONAL_RAIL: Mode.RAIL,
    MotisMode.SUBURBAN: Mode.RAIL,  # S-Bahn/suburban rail
    # Private transport
    MotisMode.CAR: Mode.CAR,
    MotisMode.CAR_PARKING: Mode.CAR,
    MotisMode.CAR_DROPOFF: Mode.CAR,
    # Meta-modes
    MotisMode.TRANSIT: Mode.TRANSIT,
    MotisMode.OTHER: Mode.OTHER,
}

INTERNAL_TO_MOTIS_MODE_MAP = {
    # Create reverse mapping, handling duplicates by preferring the primary mode
    Mode.WALK: MotisMode.WALK,
    Mode.BIKE: MotisMode.BIKE,
    Mode.BUS: MotisMode.BUS,
    Mode.TRAM: MotisMode.TRAM,
    Mode.SUBWAY: MotisMode.SUBWAY,
    Mode.RAIL: MotisMode.RAIL,
    Mode.FERRY: MotisMode.FERRY,
    Mode.CABLE_CAR: MotisMode.CABLE_CAR,
    Mode.FUNICULAR: MotisMode.FUNICULAR,
    Mode.CAR: MotisMode.CAR,
    Mode.TRANSIT: MotisMode.TRANSIT,
}


def internal_modes_to_motis_string(modes: List[Mode]) -> str:
    """
    Converts a list of internal `Mode` enums to the final comma-separated
    string required by the MOTIS API, intelligently handling the TRANSIT category.

    Example:
      [Mode.TRANSIT, Mode.WALK] -> "TRANSIT,WALK" (because MOTIS understands "TRANSIT")
      [Mode.SUBWAY, Mode.BUS, Mode.WALK] -> "SUBWAY,BUS,WALK"
    """
    motis_modes = [INTERNAL_TO_MOTIS_MODE_MAP.get(m) for m in modes]

    # Filter out any modes that couldn't be mapped
    valid_motis_modes = [m for m in motis_modes if m is not None]

    # The MOTIS API itself understands the "TRANSIT" meta-mode. If the user
    # selected our internal `Mode.TRANSIT`, we should pass "TRANSIT" directly
    # to MOTIS rather than expanding it. MOTIS will do the expansion.
    # The only time we need to expand is if our internal logic needs to know
    # the specific modes. The API call does not.

    return ",".join(sorted([m.value for m in valid_motis_modes]))
