import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List

from pydantic import ValidationError

from goatlib.routing.errors import ParsingError
from goatlib.routing.schemas.ab_routing import ABRoute, ABRouteLeg, ABRoutingRequest
from goatlib.routing.schemas.base import Location, TransportMode

from ..distance_utils import haversine_distance
from .motis_mappings import (
    INTERNAL_TO_MOTIS_MODE_MAP,
    MOTIS_CONFIG,
    MOTIS_TO_INTERNAL_MODE_MAP,
    MotisModes,
)

logger = logging.getLogger(__name__)


def convert_request_to_api_params(request: ABRoutingRequest) -> Dict[str, Any]:
    """
    Converts an internal ABRoutingRequest directly into the URL query parameters
    required by the standard MOTIS v5/plan GET API.
    """
    # Pull the relevant sections from the main config for readability
    params_cfg = MOTIS_CONFIG["request_params"]
    defaults_cfg = MOTIS_CONFIG["defaults"]

    # 1. Start with the required parameters
    api_params = {
        params_cfg["origin"]: f"{request.origin.lat},{request.origin.lon}",
        params_cfg[
            "destination"
        ]: f"{request.destination.lat},{request.destination.lon}",
    }

    # 2. Add optional parameters from the request, falling back to defaults

    # Handle time (optional)
    if request.time:
        api_params[params_cfg["time"]] = request.time.isoformat()

    # Handle number of itineraries (with default)
    api_params[params_cfg["num_itineraries"]] = (
        request.max_results or defaults_cfg["num_itineraries"]
    )

    # TODO: add the field to the ABRoutingRequest schema?
    # Handle arriveBy (with default)
    # api_params[params_cfg["arrive_by"]] = request.arrive_by or defaults_cfg["arrive_by"]

    # 3. Handle transport modes with mapping and default

    # Map internal modes to their MOTIS string values
    motis_modes = [
        INTERNAL_TO_MOTIS_MODE_MAP[m].value
        for m in request.modes
        if m in INTERNAL_TO_MOTIS_MODE_MAP
    ]

    # Use the mapped modes if any exist, otherwise use the default string
    if motis_modes:
        api_params[params_cfg["mode"]] = ",".join(motis_modes)
    else:
        api_params[params_cfg["mode"]] = defaults_cfg["mode"]

    logger.debug(f"Converted request to MOTIS API params: {api_params}")
    return api_params


def convert_response_from_motis(motis_data: Dict[str, Any]) -> List[ABRoute]:
    """
    Convert MOTIS API response to internal route objects.

    Raises:
        ParsingError: If any part of the response data is invalid.
    """
    routes = []

    response_fields = MOTIS_CONFIG["response_fields"]
    itineraries = motis_data.get(response_fields["itineraries"], [])

    if not itineraries:
        return []

    for idx, itinerary in enumerate(itineraries):
        try:
            # This will raise an exception if the itinerary is malformed
            route = _convert_itinerary_to_route(itinerary, idx)
            routes.append(route)
        except (KeyError, ValueError, ValidationError) as e:
            logger.error(f"Failed to parse MOTIS itinerary #{idx}: {e}")
            raise ParsingError(
                "Could not parse MOTIS itinerary due to invalid data."
            ) from e

    logger.info(f"Successfully converted {len(routes)} routes from MOTIS response")
    return routes


def _convert_itinerary_to_route(
    itinerary: Dict[str, Any], itinerary_idx: int
) -> ABRoute:
    """
    Convert a MOTIS itinerary to an ABRoute, calculating a simple,
    heuristic total distance.
    """
    itinerary_fields = MOTIS_CONFIG["itinerary_fields"]

    route_duration = itinerary[itinerary_fields["duration"]]
    original_legs_data = itinerary[itinerary_fields["legs"]]

    if not original_legs_data:
        raise ParsingError(f"Itinerary {itinerary_idx} has no legs.")

    distance = 0.0
    parsed_legs = [
        _convert_leg_to_ab_leg(leg, itinerary_idx, leg_idx)
        for leg_idx, leg in enumerate(original_legs_data)
    ]
    for leg in parsed_legs:
        distance += leg.distance

    # TODO: improve distance calculation using polylines

    return ABRoute(
        route_id=f"motis_route_{itinerary_idx}",
        duration=route_duration,
        distance=distance,
        departure_time=parsed_legs[0].departure_time,
        legs=parsed_legs,
    )


def _convert_leg_to_ab_leg(
    leg: Dict[str, Any], itinerary_idx: int, leg_idx: int
) -> ABRouteLeg:
    """
    STRICTLY converts a MOTIS leg to an ABRouteLeg object, but
    DOES NOT calculate or trust the distance field.
    """
    leg_fields = MOTIS_CONFIG["leg_fields"]

    mode = _extract_transport_mode(leg)
    origin, destination = _extract_locations(leg)
    departure_time, arrival_time = _extract_timing(leg)

    distance = leg.get(leg_fields["distance"], 0.0)
    if distance <= 0:
        # in case of public transport leg, calculate distance from lat/lon with haversine
        distance = haversine_distance(
            origin.lat, origin.lon, destination.lat, destination.lon
        )

    duration = leg[leg_fields["duration"]]
    if duration <= 0:
        # in case of public transport leg, calculate duration from departure and arrival times
        time_difference: timedelta = arrival_time - departure_time
        duration = int(time_difference.total_seconds())

    geometry = leg.get(leg_fields.get("geometry", ""), None)

    return ABRouteLeg(
        leg_id=f"i{itinerary_idx}_l{leg_idx}",
        mode=mode,
        origin=origin,
        destination=destination,
        departure_time=departure_time,
        arrival_time=arrival_time,
        duration=duration,
        distance=distance,
        geometry=geometry,
    )


def _extract_transport_mode(leg: Dict[str, Any]) -> TransportMode:
    """Extract and convert transport mode from MOTIS leg."""
    leg_fields = MOTIS_CONFIG["leg_fields"]
    mode_str = leg[leg_fields["mode"]]

    if mode_str in MOTIS_TO_INTERNAL_MODE_MAP:
        return MOTIS_TO_INTERNAL_MODE_MAP[mode_str]

    motis_mode = getattr(MotisModes, mode_str, None)
    if motis_mode and motis_mode in MOTIS_TO_INTERNAL_MODE_MAP:
        return MOTIS_TO_INTERNAL_MODE_MAP[motis_mode]

    logger.warning(f"Unknown mode {mode_str} in MOTIS leg")
    return TransportMode.WALK


def _extract_locations(leg: Dict[str, Any]) -> tuple[Location, Location]:
    """Extract origin and destination locations from MOTIS leg."""
    leg_fields = MOTIS_CONFIG["leg_fields"]
    location_fields = MOTIS_CONFIG["location_fields"]

    from_data = leg[leg_fields["from"]]
    to_data = leg[leg_fields["to"]]

    origin = Location(
        lat=from_data[location_fields["lat"]],
        lon=from_data[location_fields["lon"]],
    )

    destination = Location(
        lat=to_data[location_fields["lat"]],
        lon=to_data[location_fields["lon"]],
    )

    return origin, destination


def _extract_timing(leg: Dict[str, Any]) -> tuple[datetime, datetime]:
    """Extract departure and arrival times from MOTIS leg."""
    leg_fields = MOTIS_CONFIG["leg_fields"]
    start_time_str = leg[leg_fields["start_time"]]
    end_time_str = leg[leg_fields["end_time"]]

    # Convert ISO string timestamps to datetime objects
    departure_time = (
        datetime.fromisoformat(start_time_str.replace("Z", "+00:00"))
        if start_time_str
        else datetime.now()
    )

    arrival_time = (
        datetime.fromisoformat(end_time_str.replace("Z", "+00:00"))
        if end_time_str
        else departure_time  # Use departure time if no end time
    )
    # TODO: fix it properly
    # Ensure arrival is after departure
    if arrival_time <= departure_time:
        arrival_time = departure_time + timedelta(minutes=5)

    return departure_time, arrival_time
