from enum import StrEnum
from typing import Any, List

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


# MOTIS_CONFIG for a standard MOTIS v5/plan API
# "internal" : "motis_param"
MOTIS_CONFIG = {
    # =====================================================================
    # Request Parameters (for the GET API)
    # =====================================================================
    "request_params": {
        "origin": "fromPlace",  # e.g., "52.52,13.405"
        "destination": "toPlace",  # e.g., "53.5511,9.9937"
        "time": "time",  # ISO 8601 string, e.g., "2025-11-05T17:22:00Z"
        "mode": "mode",  # Comma-separated string, e.g., "TRANSIT,WALK"
        "num_itineraries": "numItineraries",  # Integer for number of results to compute at least
        "max_results": "maxItineraries",  # Max number of itineraries to return
        "time_is_arrival": "arriveBy",  # Boolean
        "detailed_transters": "detailedTransfers",  # Boolean for detailed transfer info
    },
    # =====================================================================
    # Response Structure Mappings (what we expect to receive)
    # =====================================================================
    "response_fields": {
        "itineraries": "itineraries",  # The primary list of journey objects
    },
    "itinerary_fields": {
        "duration": "duration",  # Total duration in seconds
        "start_time": "startTime",  # ISO 8601 string
        "end_time": "endTime",  # ISO 8601 string
        "legs": "legs",  # The list of leg objects
    },
    "leg_fields": {
        "mode": "mode",  # String like "WALK", "RAIL", "BUS"
        "duration": "duration",  # Duration of the leg in seconds
        "distance": "distance",  # "For non-transit legs the distance traveled while traversing this leg in meters"
        "start_time": "startTime",  # ISO 8601 string
        "end_time": "endTime",  # ISO 8601 string
        "from": "from",  # The origin location object for this leg
        "to": "to",  # The destination location object for this leg
        # "geometry": "legGeometry",  # The nested object containing the polyline
    },
    "location_fields": {
        "lat": "lat",  # Latitude coordinate
        "lon": "lon",  # Longitude coordinate
        "name": "name",  # Name of the station or place
    },
    # =====================================================================
    # Default Values for API Requests (internal key : default value)
    # =====================================================================
    "defaults": {
        "num_itineraries": 5,
        "max_results": 5,
        "time_is_arrival": False,
        "mode": "TRANSIT",
        "detailed_transters": False,
    },
    "endpoints": {
        "plan": "/api/v5/plan",
        "one_to_all": "/api/v1/one-to-all",
    },
}  # Mode mappings between MOTIS and internal representations
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


# Utility functions for working with MOTIS_CONFIG
def get_motis_param(internal_key: str) -> str:
    """Get the MOTIS parameter name for an internal key."""
    return MOTIS_CONFIG["request_params"].get(internal_key, internal_key)


def get_motis_field(section: str, internal_key: str) -> str:
    """Get the MOTIS field name for an internal key in a specific section."""
    section_config = MOTIS_CONFIG.get(section, {})
    return section_config.get(internal_key, internal_key)


def get_motis_default(key: str) -> Any:
    """Get a default value for a MOTIS parameter."""
    return MOTIS_CONFIG["defaults"].get(key)


def get_alternative_params(param_type: str) -> List[str]:
    """Get alternative parameter names for compatibility with different MOTIS implementations."""
    return MOTIS_CONFIG["alternative_params"].get(param_type, [])


def build_motis_url(base_url: str, endpoint: str = "plan") -> str:
    """Build a complete MOTIS API URL."""
    if base_url.endswith("/"):
        base_url = base_url.rstrip("/")

    endpoint_path = MOTIS_CONFIG["endpoints"].get(endpoint, f"/api/v5/{endpoint}")
    return f"{base_url}{endpoint_path}"
