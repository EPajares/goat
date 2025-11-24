import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List

from pydantic import ValidationError

from goatlib.analysis.schemas.vector import BufferParams
from goatlib.routing.errors import ParsingError
from goatlib.routing.schemas.ab_routing import (
    ABLeg,
    ABRoute,
    ABRoutingRequest,
    ABRoutingResponse,
)
from goatlib.routing.schemas.base import Location, Mode
from goatlib.routing.schemas.catchment_area_transit import (
    CatchmentAreaPolygon,
    TransitCatchmentAreaRequest,
    TransitCatchmentAreaResponse,
)

from ..distance_utils import haversine_distance
from .motis_mappings import (
    INTERNAL_TO_MOTIS_MODE_MAP,
    MOTIS_TO_INTERNAL_MODE_MAP,
    MotisMode,
)
from .motis_settings import motis_settings

logger = logging.getLogger(__name__)


def translate_to_motis_request(request: ABRoutingRequest) -> Dict[str, Any]:
    """
    Converts an internal ABRoutingRequest directly into the URL query parameters
    required by the standard MOTIS v5/plan GET API.
    """
    # Pull the relevant sections from the settings for readability
    params = motis_settings.request_params
    defaults = motis_settings.defaults

    # Start with the required MOTIS parameters
    api_params = {
        params.origin: f"{request.origin.lat},{request.origin.lon}",
        params.destination: f"{request.destination.lat},{request.destination.lon}",
        params.detailed_transfers: (
            request.detailed_transfers
            if request.detailed_transfers is not None
            else defaults.detailed_transfers
        ),
    }

    # Add optional parameters from the request, falling back to defaults

    # Handle time (optional)
    if request.time:
        api_params[params.time] = request.time.isoformat()

    # Handle internal default parameters
    api_params[params.num_itineraries] = defaults.num_itineraries

    # Handle arriveBy (with default)
    api_params[params.time_is_arrival] = (
        request.time_is_arrival
        if request.time_is_arrival is not None
        else defaults.time_is_arrival
    )

    # Handle transport modes with mapping and default

    # Map internal modes to their MOTIS string values
    motis_modes = [
        INTERNAL_TO_MOTIS_MODE_MAP[m].value
        for m in request.modes
        if m in INTERNAL_TO_MOTIS_MODE_MAP
    ]

    # Use the mapped modes if any exist, otherwise use the default
    if motis_modes:
        api_params[params.transit_modes] = ",".join(motis_modes)
    else:
        # Use default transit modes
        default_modes = [mode.value for mode in defaults.transit_modes]
        api_params[params.transit_modes] = ",".join(default_modes)

    return api_params


def parse_motis_response(motis_data: Dict[str, Any]) -> ABRoutingResponse:
    """
    Convert MOTIS API response to internal route objects.

    Raises:
        ParsingError: If any part of the response data is invalid.
    """
    routes = []

    # MOTIS response has "itineraries" at the top level
    itineraries = motis_data.get("itineraries", [])

    if itineraries:
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

    return ABRoutingResponse(routes=routes)


def _convert_itinerary_to_route(
    itinerary: Dict[str, Any], itinerary_idx: int
) -> ABRoute:
    """Convert a MOTIS itinerary to an ABRoute."""
    itinerary_fields = motis_settings.itinerary_fields

    original_legs_data = itinerary[itinerary_fields.legs]

    if not original_legs_data:
        raise ParsingError(f"Itinerary {itinerary_idx} has no legs.")

    parsed_legs = [
        _convert_leg_to_ab_leg(leg, itinerary_idx, leg_idx)
        for leg_idx, leg in enumerate(original_legs_data)
    ]

    # Calculate total distance by summing all leg distances
    total_distance = sum(
        leg.distance for leg in parsed_legs if leg.distance is not None
    )

    return ABRoute(
        route_id=f"motis_route_{itinerary_idx}",
        duration=itinerary[itinerary_fields.duration],
        distance=total_distance,
        departure_time=parsed_legs[0].departure_time,
        legs=parsed_legs,
    )


def _convert_leg_to_ab_leg(
    leg: Dict[str, Any], itinerary_idx: int, leg_idx: int
) -> ABLeg:
    """Convert a MOTIS leg to an ABLeg object."""
    leg_fields = motis_settings.leg_fields

    mode = _extract_transport_mode(leg)
    origin, destination = _extract_locations(leg)
    departure_time, arrival_time = _extract_timing(leg)

    distance = leg.get(leg_fields.distance, 0.0)

    # If MOTIS doesn't provide distance, calculate it using coordinate distance
    if distance <= 0:
        # Use Haversine distance for all modes when MOTIS doesn't provide distance
        distance = haversine_distance(
            origin.lat, origin.lon, destination.lat, destination.lon
        )

    duration = leg[leg_fields.duration]
    if duration <= 0:
        # If MOTIS doesn't provide duration, calculate from actual times
        time_difference: timedelta = arrival_time - departure_time
        duration = int(time_difference.total_seconds())
    else:
        # Verify that MOTIS duration matches the actual time difference
        actual_duration = int((arrival_time - departure_time).total_seconds())
        if abs(duration - actual_duration) > 60:  # More than 1 minute difference
            logger.warning(
                f"MOTIS duration ({duration}s) doesn't match actual time difference ({actual_duration}s), using calculated duration"
            )
            duration = actual_duration

    return ABLeg(
        leg_id=f"i{itinerary_idx}_l{leg_idx}",
        mode=mode,
        origin=origin,
        destination=destination,
        departure_time=departure_time,
        arrival_time=arrival_time,
        duration=duration,
        distance=distance,
    )


def _extract_transport_mode(leg: Dict[str, Any]) -> Mode:
    """Extract and convert transport mode from MOTIS leg."""
    leg_fields = motis_settings.leg_fields
    mode_str = leg[leg_fields.mode]

    if mode_str in MOTIS_TO_INTERNAL_MODE_MAP:
        return MOTIS_TO_INTERNAL_MODE_MAP[mode_str]

    motis_mode = getattr(MotisMode, mode_str, None)
    if motis_mode and motis_mode in MOTIS_TO_INTERNAL_MODE_MAP:
        return MOTIS_TO_INTERNAL_MODE_MAP[motis_mode]

    logger.warning(f"Unknown mode {mode_str} in MOTIS leg")
    return Mode.WALK


def _extract_locations(leg: Dict[str, Any]) -> tuple[Location, Location]:
    """Extract origin and destination locations from MOTIS leg."""
    leg_fields = motis_settings.leg_fields
    location_fields = motis_settings.location_fields

    from_data = leg[leg_fields.from_loc]
    to_data = leg[leg_fields.to_loc]

    origin = Location(
        lat=from_data[location_fields.lat],
        lon=from_data[location_fields.lon],
    )

    destination = Location(
        lat=to_data[location_fields.lat],
        lon=to_data[location_fields.lon],
    )

    return origin, destination


def _extract_timing(leg: Dict[str, Any]) -> tuple[datetime, datetime]:
    """Extract departure and arrival times from MOTIS leg."""
    leg_fields = motis_settings.leg_fields
    start_time_str = leg[leg_fields.start_time]
    end_time_str = leg[leg_fields.end_time]

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

    # Check if we have valid times from MOTIS
    if arrival_time <= departure_time:
        # If MOTIS provided invalid times, try to use duration from MOTIS
        duration_from_motis = leg.get(leg_fields.duration, 0)
        if duration_from_motis > 0:
            # Use MOTIS duration to calculate correct arrival time
            arrival_time = departure_time + timedelta(seconds=duration_from_motis)
        else:
            # Last resort: assume minimum 1 minute duration
            arrival_time = departure_time + timedelta(minutes=1)
            logger.warning(
                "MOTIS provided invalid timing data for leg, using minimal duration"
            )

    return departure_time, arrival_time


# =====================================================================
# ONE-TO-ALL CONVERTER FUNCTIONS
# =====================================================================


def translate_to_motis_one_to_all_request(
    request: TransitCatchmentAreaRequest,
) -> Dict[str, Any]:
    """
    Converts a TransitCatchmentAreaRequest to MOTIS one-to-all API parameters.

    Args:
        request: Internal transit catchment area request

    Returns:
        Dictionary of MOTIS one-to-all API parameters
    """
    # Get the settings for one-to-all parameters
    params = motis_settings.one_to_all_params
    defaults = motis_settings.one_to_all_defaults

    # Extract the single starting point (transit only supports one)
    lat = request.starting_points.latitude[0]
    lon = request.starting_points.longitude[0]

    # Build the API parameters
    api_params = {
        params.origin: f"{lat},{lon}",
        params.max_travel_time: request.travel_cost.max_traveltime,
        params.arrive_by: False,  # Always one-to-all for now
    }

    # Add transit modes
    motis_transit_modes = []
    for mode in request.transit_modes:
        # Map our transit modes to MOTIS modes if needed
        motis_mode = mode.value.upper()
        motis_transit_modes.append(motis_mode)

    if motis_transit_modes:
        api_params[params.transit_modes] = ",".join(motis_transit_modes)
    else:
        api_params[params.transit_modes] = ",".join(defaults.transit_modes)

    # Add access/egress modes
    access_mode = request.access_mode.value.upper()
    egress_mode = request.egress_mode.value.upper()
    api_params[params.pre_transit_modes] = access_mode
    api_params[params.post_transit_modes] = egress_mode

    # Add routing settings if provided
    if request.routing_settings:
        if request.routing_settings.max_transfers:
            api_params[params.max_transfers] = request.routing_settings.max_transfers

        # Convert walk/bike settings to MOTIS parameters
        if request.routing_settings.walk_settings:
            walk_time_seconds = request.routing_settings.walk_settings.max_time * 60
            api_params[params.max_pre_transit_time] = walk_time_seconds
            api_params[params.max_post_transit_time] = walk_time_seconds
            # Note: MOTIS uses m/s for speed, our settings use km/h
            walk_speed_ms = request.routing_settings.walk_settings.speed / 3.6
            api_params[params.pedestrian_speed] = walk_speed_ms

        if request.routing_settings.bike_settings:
            bike_speed_ms = request.routing_settings.bike_settings.speed / 3.6
            api_params[params.cycling_speed] = bike_speed_ms

    # Add time if provided (use current time if not specified)
    if hasattr(request, "departure_time") and request.departure_time:
        api_params[params.time] = request.departure_time.isoformat()
    else:
        api_params[params.time] = datetime.now().isoformat()

    # Add default values for other parameters
    api_params[params.pedestrian_profile] = defaults.pedestrian_profile
    api_params[params.elevation_costs] = defaults.elevation_costs
    api_params[params.use_routed_transfers] = defaults.use_routed_transfers

    return api_params


def parse_motis_one_to_all_response(
    motis_data: Dict[str, Any], request: TransitCatchmentAreaRequest
) -> TransitCatchmentAreaResponse:
    """
    Convert MOTIS one-to-all API response to TransitCatchmentAreaResponse.

    Args:
        motis_data: Raw MOTIS one-to-all response
        request: Original request (needed for cutoff processing)

    Returns:
        TransitCatchmentAreaResponse with polygons

    Raises:
        ParsingError: If the response data is invalid
    """
    try:
        fields = motis_settings.one_to_all_fields

        # Extract reachable locations from MOTIS response
        reachable_locations = motis_data.get(fields.all, [])

        if not reachable_locations:
            logger.warning("No reachable locations found in MOTIS one-to-all response")
            return TransitCatchmentAreaResponse(polygons=[])

        # Group locations by travel time cutoffs
        cutoffs = request.travel_cost.cutoffs
        polygons = []

        # Note: Minimal validation approach adopted here
        # - Input validation happens at Pydantic schema level
        # - Only critical coordinate bounds checking retained for geometry calculation safety
        for cutoff in cutoffs:
            # Find all locations reachable within this cutoff (in minutes)
            reachable_within_cutoff = []

            for loc in reachable_locations:
                # Get travel duration in minutes from MOTIS
                duration_minutes = loc.get(fields.travel_time, 0)

                if duration_minutes <= cutoff:
                    # Extract place information
                    place = loc.get(fields.place, {})
                    if place:
                        lat = place.get(fields.lat)
                        lon = place.get(fields.lon)

                        # Minimal coordinate validation - only check existence and bounds
                        if (
                            lat is None
                            or lon is None
                            or not (-90 <= lat <= 90)
                            or not (-180 <= lon <= 180)
                        ):
                            logger.warning(
                                f"Invalid coordinates in MOTIS location: lat={lat}, lon={lon}"
                            )
                            continue

                        reachable_within_cutoff.append(
                            {
                                "lat": lat,
                                "lon": lon,
                                "duration_minutes": duration_minutes,
                                "name": place.get(fields.name, "Unknown"),
                                "stop_id": place.get(fields.stop_id, ""),
                            }
                        )

            if reachable_within_cutoff:
                # Create polygon from reachable points
                polygon_geom = _create_polygon_from_points(reachable_within_cutoff)

                polygon = CatchmentAreaPolygon(
                    travel_time=cutoff, geometry=polygon_geom
                )
                polygons.append(polygon)

        return TransitCatchmentAreaResponse(
            polygons=polygons,
            metadata={
                "total_locations": len(reachable_locations),
                "source": "motis_one_to_all",
                "request_max_travel_time": request.travel_cost.max_traveltime,
                "cutoffs_requested": request.travel_cost.cutoffs,
                "polygons_generated": len(polygons),
                "locations_with_valid_coordinates": sum(
                    len(polygon.geometry.get("coordinates", [[]])[0])
                    for polygon in polygons
                    if polygon.geometry.get("coordinates")
                ),
            },
        )

    except (KeyError, ValueError) as e:
        logger.error(f"Failed to parse MOTIS one-to-all response: {e}")
        raise ParsingError(
            "Could not parse MOTIS one-to-all response due to invalid data."
        ) from e


def _create_polygon_from_points(
    reachable_locations: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Create a simple polygon geometry from reachable location points.
    This is a temporary implementation using bounding box approach.

    Args:
        reachable_locations: List of reachable location data with lat/lon

    Returns:
        GeoJSON-style polygon geometry
    """
    if not reachable_locations:
        return {"type": "Polygon", "coordinates": []}

    # Extract coordinates
    coordinates = []
    for loc in reachable_locations:
        lat = loc.get("lat", 0)
        lon = loc.get("lon", 0)
        if lat != 0 and lon != 0:
            coordinates.append([lon, lat])  # GeoJSON uses [lon, lat] order

    if len(coordinates) < 3:
        # Not enough points for a polygon, return empty
        return {"type": "Polygon", "coordinates": []}

    # Create a simple bounding box
    lons = [coord[0] for coord in coordinates]
    lats = [coord[1] for coord in coordinates]

    min_lon, max_lon = min(lons), max(lons)
    min_lat, max_lat = min(lats), max(lats)

    # Create bounding box polygon
    bbox_coordinates = [
        [
            [min_lon, min_lat],
            [max_lon, min_lat],
            [max_lon, max_lat],
            [min_lon, max_lat],
            [min_lon, min_lat],  # Close the polygon
        ]
    ]

    return {"type": "Polygon", "coordinates": bbox_coordinates}


def create_bus_station_buffers(
    reachable_locations: List[Dict[str, Any]],
    buffer_distances: List[float] = [200, 400, 600],
    dissolve: bool = True,
    output_path: str = "/tmp/bus_station_buffers.geojson",
) -> BufferParams:
    """
    Create BufferParams for buffering bus stations from MOTIS one-to-all response.

    Args:
        reachable_locations: List of reachable location data from MOTIS
        buffer_distances: List of buffer distances in meters (default: 200m, 400m, 600m)
        dissolve: Whether to dissolve overlapping buffers (default: True)
        output_path: Output path for buffered geometries

    Returns:
        BufferParams configured for bus station buffering

    Example:
        >>> # After getting MOTIS one-to-all response
        >>> reachable_locations = motis_response.get("all", [])
        >>>
        >>> # Create buffer configuration
        >>> buffer_config = create_bus_station_buffers(
        ...     reachable_locations=reachable_locations,
        ...     buffer_distances=[300, 500, 800],  # 300m, 500m, 800m buffers
        ...     dissolve=True,
        ...     output_path="/output/munich_bus_station_buffers.geojson"
        ... )
        >>>
        >>> # Use with your spatial analysis library
        >>> # buffer_results = your_gis_processor.process(buffer_config)
    """
    from goatlib.analysis.schemas.vector import BufferParams

    # Create temporary input file path for bus station points
    input_path = "/tmp/bus_stations_points.geojson"

    # Log information about the stations
    logger.info(f"Creating buffers for {len(reachable_locations)} bus stations")
    logger.info(f"Buffer distances: {buffer_distances} meters")
    logger.info(f"Dissolve overlapping buffers: {dissolve}")

    # Create BufferParams with the provided configuration
    buffer_params = BufferParams(
        input_path=input_path,
        output_path=output_path,
        distances=buffer_distances,
        units="meters",
        dissolve=dissolve,
        num_triangles=16,  # Smoother buffers for transit stations
        cap_style="CAP_ROUND",  # Round caps for stations
        join_style="JOIN_ROUND",  # Round joins for smoother appearance
        output_crs="EPSG:4326",  # WGS84 for compatibility
        output_name="bus_station_buffers",
    )

    return buffer_params


def extract_bus_stations_for_buffering(
    motis_data: Dict[str, Any], min_frequency: int = 1
) -> List[Dict[str, Any]]:
    """
    Extract bus station information from MOTIS one-to-all response for buffer analysis.

    Args:
        motis_data: Raw MOTIS one-to-all response
        min_frequency: Minimum frequency threshold for station inclusion

    Returns:
        List of bus station data suitable for buffering
    """
    fields = motis_settings.one_to_all_fields
    stations = []

    reachable_locations = motis_data.get(fields.all, [])

    for loc in reachable_locations:
        place = loc.get(fields.place, {})
        if place:
            lat = place.get(fields.lat)
            lon = place.get(fields.lon)
            station_name = place.get(fields.name, "Unknown Station")
            duration = loc.get(fields.travel_time, 0)

            # Basic coordinate validation
            if (
                lat is not None
                and lon is not None
                and -90 <= lat <= 90
                and -180 <= lon <= 180
            ):
                stations.append(
                    {
                        "name": station_name,
                        "lat": lat,
                        "lon": lon,
                        "duration_minutes": duration,
                        "stop_id": place.get(fields.stop_id, ""),
                        "coordinates": [lon, lat],  # GeoJSON format
                    }
                )

    logger.info(f"Extracted {len(stations)} valid bus stations for buffering")
    return stations
