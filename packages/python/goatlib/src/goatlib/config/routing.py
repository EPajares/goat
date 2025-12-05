from goatlib.routing.schemas.catchment_area_active import (
    CatchmentAreaRoutingTypeActiveMobility,
    CatchmentAreaRoutingTypeCar,
)

# --- Road Network Configuration ---
_SHARED_ACTIVE_MOBILITY_CLASSES = (
    "primary",
    "secondary",
    "tertiary",
    "residential",
    "living_street",
    "trunk",
    "unclassified",
    "service",
    "pedestrian",
    "footway",
    "steps",
    "path",
    "track",
    "cycleway",
    "bridleway",
    "unknown",
)

_CAR_CLASSES = (
    "motorway",
    "primary",
    "secondary",
    "tertiary",
    "residential",
    "living_street",
    "trunk",
    "unclassified",
    "service",
    "track",
)

VALID_ROAD_CLASSES = {
    CatchmentAreaRoutingTypeActiveMobility.walking: _SHARED_ACTIVE_MOBILITY_CLASSES,
    CatchmentAreaRoutingTypeActiveMobility.bicycle: _SHARED_ACTIVE_MOBILITY_CLASSES,
    CatchmentAreaRoutingTypeActiveMobility.wheelchair: _SHARED_ACTIVE_MOBILITY_CLASSES,
    CatchmentAreaRoutingTypeCar.car: _CAR_CLASSES,
}
# --- Specific Routing Parameters ---
BICYCLE_SPEED_FOOTWAYS = 5  # km/h

H3_CELL_RESOLUTION = {
    CatchmentAreaRoutingTypeActiveMobility.walking: 10,
    CatchmentAreaRoutingTypeActiveMobility.bicycle: 9,
    CatchmentAreaRoutingTypeActiveMobility.pedelec: 9,
    CatchmentAreaRoutingTypeCar.car: 8,
}
