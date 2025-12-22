from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from goatlib.routing.adapters.motis.motis_mappings import MotisMode

# =====================================================================
# NESTED MODELS FOR TYPE-SAFE CONFIGURATION
# =====================================================================


class RequestParams(BaseSettings):
    """Maps internal keys to MOTIS v5 Plan API request parameter names."""

    # Location parameters
    origin: str = "fromPlace"
    destination: str = "toPlace"
    via: str = "via"  # Intermediate via location
    via_minimum_stay: str = "viaMinimumStay"

    # Time and date parameters
    time: str = "time"
    time_is_arrival: str = "arriveBy"

    # Travel time and routing parameters
    max_travel_time: str = "maxTravelTime"
    max_transfers: str = "maxTransfers"
    min_transfer_time: str = "minTransferTime"
    additional_transfer_time: str = "additionalTransferTime"
    transfer_time_factor: str = "transferTimeFactor"

    # Routing configuration
    max_matching_distance: str = "maxMatchingDistance"
    use_routed_transfers: str = "useRoutedTransfers"
    detailed_transfers: str = "detailedTransfers"
    join_interlined_legs: str = "joinInterlinedLegs"

    # Transport modes
    transit_modes: str = "transitModes"
    direct_modes: str = "directModes"
    pre_transit_modes: str = "preTransitModes"
    post_transit_modes: str = "postTransitModes"

    # Accessibility and speed parameters
    pedestrian_profile: str = "pedestrianProfile"
    pedestrian_speed: str = "pedestrianSpeed"
    cycling_speed: str = "cyclingSpeed"
    elevation_costs: str = "elevationCosts"

    # Transit time constraints
    max_pre_transit_time: str = "maxPreTransitTime"
    max_post_transit_time: str = "maxPostTransitTime"
    max_direct_time: str = "maxDirectTime"

    # Search window and pagination
    num_itineraries: str = "numItineraries"
    max_itineraries: str = "maxItineraries"
    page_cursor: str = "pageCursor"
    timetable_view: str = "timetableView"
    search_window: str = "searchWindow"

    # Performance and optimization
    fastest_direct_factor: str = "fastestDirectFactor"
    timeout: str = "timeout"
    algorithm: str = "algorithm"

    # Transport requirements
    require_bike_transport: str = "requireBikeTransport"
    require_car_transport: str = "requireCarTransport"

    # Output configuration
    with_fares: str = "withFares"
    with_scheduled_skipped_stops: str = "withScheduledSkippedStops"
    language: str = "language"


class ItineraryFields(BaseSettings):
    """Expected fields within a single itinerary object ."""

    duration: str = "duration"
    start_time: str = "startTime"
    end_time: str = "endTime"
    legs: str = "legs"
    transfers: str = "transfers"
    fare_transfers: str = "fareTransfers"


class LegFields(BaseSettings):
    """Expected fields within a single leg object ."""

    mode: str = "mode"
    duration: str = "duration"
    distance: str = "distance"
    start_time: str = "startTime"
    end_time: str = "endTime"
    scheduled_start_time: str = "scheduledStartTime"
    scheduled_end_time: str = "scheduledEndTime"
    real_time: str = "realTime"
    scheduled: str = "scheduled"
    from_loc: str = "from"  # Renamed to avoid Python keyword 'from'
    to_loc: str = "to"  # Renamed to avoid confusion
    leg_geometry: str = "legGeometry"  # Encoded polyline geometry
    intermediate_stops: str = "intermediateStops"
    steps: str = "steps"  # Turn-by-turn instructions

    # Transit-specific fields
    headsign: str = "headsign"  # e.g., "U2 Pankow"
    trip_to: str = "tripTo"  # Final stop of trip
    route_id: str = "routeId"
    direction_id: str = "directionId"
    route_color: str = "routeColor"
    route_text_color: str = "routeTextColor"
    route_type: str = "routeType"
    agency_name: str = "agencyName"
    agency_url: str = "agencyUrl"
    agency_id: str = "agencyId"
    trip_id: str = "tripId"  # The GTFS trip_id
    route_short_name: str = "routeShortName"
    route_long_name: str = "routeLongName"
    trip_short_name: str = "tripShortName"
    display_name: str = "displayName"
    cancelled: str = "cancelled"
    source: str = "source"
    interline_with_previous_leg: str = "interlineWithPreviousLeg"
    fare_transfer_index: str = "fareTransferIndex"
    effective_fare_leg_index: str = "effectiveFareLegIndex"
    alerts: str = "alerts"
    looped_calendar_since: str = "loopedCalendarSince"

    # Rental and sharing
    rental: str = "rental"


class LocationFields(BaseSettings):
    """Expected fields within a location/place object ."""

    lat: str = "lat"
    lon: str = "lon"
    name: str = "name"
    stop_id: str = "stopId"  # The stop ID
    parent_id: str = "parentId"  # Parent stop ID if not root stop
    importance: str = "importance"  # Stop importance 0-1
    level: str = "level"  # OpenStreetMap level
    tz: str = "tz"  # Timezone name
    arrival: str = "arrival"  # Arrival time
    departure: str = "departure"  # Departure time
    scheduled_arrival: str = "scheduledArrival"  # Scheduled arrival time
    scheduled_departure: str = "scheduledDeparture"  # Scheduled departure time
    scheduled_track: str = "scheduledTrack"  # Scheduled track/platform
    track: str = "track"  # Current track/platform with real-time updates
    description: str = "description"  # Location description
    vertex_type: str = "vertexType"  # NORMAL, BIKESHARE, TRANSIT
    pickup_type: str = "pickupType"  # Pickup type (NORMAL, NOT_ALLOWED)
    dropoff_type: str = "dropoffType"  # Dropoff type (NORMAL, NOT_ALLOWED)
    cancelled: str = "cancelled"  # Whether stop is cancelled
    alerts: str = "alerts"  # Service alerts
    # FLEX transport fields
    flex: str = "flex"  # Flex location area/group name
    flex_id: str = "flexId"  # Flex location area/group ID
    flex_start_pickup_dropoff_window: str = "flexStartPickupDropOffWindow"
    flex_end_pickup_dropoff_window: str = "flexEndPickupDropOffWindow"


class Defaults(BaseSettings):
    """Default values for API requests ."""

    num_itineraries: int = 5
    max_itineraries: int = 50  # From OpenAPI spec, no explicit default mentioned
    time_is_arrival: bool = False
    transit_modes: list = [MotisMode.TRANSIT]  # Default allows all transit modes
    direct_modes: list = [MotisMode.WALK]  # Default walking connections
    pre_transit_modes: list = [MotisMode.WALK]  # Default pre-transit walking
    post_transit_modes: list = [MotisMode.WALK]  # Default post-transit walking
    max_transfers: int = 99  # High default as per OpenAPI spec
    search_window: int = 900  # 15 minutes in seconds
    max_matching_distance: int = 25  # 25 meters default
    pedestrian_profile: str = "FOOT"  # Default accessibility profile
    elevation_costs: str = "NONE"  # Default no elevation costs
    timetable_view: bool = True  # Default timetable view
    detailed_transfers: bool = True  # Default detailed transfers
    join_interlined_legs: bool = True  # Default join interlined legs
    use_routed_transfers: bool = False  # Default basic transfers
    require_bike_transport: bool = False  # Default no bike requirement
    require_car_transport: bool = False  # Default no car requirement
    with_fares: bool = False  # Default no fare information
    with_scheduled_skipped_stops: bool = False  # Default no skipped stops
    min_transfer_time: int = 0  # Default 0 minutes
    additional_transfer_time: int = 0  # Default 0 minutes
    transfer_time_factor: float = 1.0  # Default 1.0 factor
    max_pre_transit_time: int = 900  # Default 15 minutes
    max_post_transit_time: int = 900  # Default 15 minutes
    max_direct_time: int = 1800  # Default 30 minutes
    fastest_direct_factor: float = 1.0  # Default 1.0 factor
    algorithm: str = "PONG"  # Default algorithm from OpenAPI spec


class Endpoints(BaseSettings):
    """API endpoints ."""

    plan: str = "/api/v5/plan"  # Main routing endpoint
    trip: str = "/api/v5/trip"  # Get trip as itinerary
    stoptimes: str = "/api/v5/stoptimes"  # Stop departures/arrivals
    map_trips: str = "/api/v5/map/trips"  # Map trips endpoint

    # v1 endpoints still available
    one_to_many: str = "/api/v1/one-to-many"  # Street routing one to many
    one_to_all: str = "/api/v1/one-to-all"  # Reachable locations
    geocode: str = "/api/v1/geocode"  # Geocoding
    reverse_geocode: str = "/api/v1/reverse-geocode"  # Reverse geocoding
    map_initial: str = "/api/v1/map/initial"  # Initial map location
    map_stops: str = "/api/v1/map/stops"  # Map stops
    map_levels: str = "/api/v1/map/levels"  # Map levels
    rentals: str = "/api/v1/rentals"  # Rental information

    # Debug endpoints
    debug_transfers: str = "/api/debug/transfers"  # Debug transfers


class OneToAllParams(BaseSettings):
    """Maps internal keys to MOTIS one-to-all API request parameter names."""

    # Core location and travel constraints
    origin: str = "one"  # Origin point for one-to-all calculation
    max_travel_time: str = "maxTravelTime"  # In minutes
    time: str = "time"  # Time in ISO date-time format
    arrive_by: str = "arriveBy"  # true = all to one, false = one to all

    # Transport mode configuration
    transit_modes: str = "transitModes"  # Comma-separated transit modes
    pre_transit_modes: str = (
        "preTransitModes"  # How to reach transit (WALK, BIKE, etc.)
    )
    post_transit_modes: str = (
        "postTransitModes"  # How to leave transit (WALK, BIKE, etc.)
    )

    # Advanced routing parameters
    max_transfers: str = "maxTransfers"
    min_transfer_time: str = "minTransferTime"  # Minimum transfer time in minutes
    additional_transfer_time: str = (
        "additionalTransferTime"  # Additional transfer time in minutes
    )
    transfer_time_factor: str = (
        "transferTimeFactor"  # Factor to multiply transfer times
    )

    # Performance and quality settings
    max_matching_distance: str = (
        "maxMatchingDistance"  # Maximum matching distance in meters
    )
    use_routed_transfers: str = "useRoutedTransfers"  # Whether to use routed transfers
    pedestrian_profile: str = "pedestrianProfile"  # FOOT or WHEELCHAIR
    pedestrian_speed: str = "pedestrianSpeed"  # Average pedestrian speed
    cycling_speed: str = "cyclingSpeed"  # Average cycling speed
    elevation_costs: str = "elevationCosts"  # NONE, LOW, HIGH

    # Transit requirements
    require_bike_transport: str = "requireBikeTransport"  # Require bike carriage
    require_car_transport: str = "requireCarTransport"  # Require car carriage

    # Time constraints for street legs
    max_pre_transit_time: str = (
        "maxPreTransitTime"  # Max time to reach transit (seconds)
    )
    max_post_transit_time: str = "maxPostTransitTime"  # Max time from transit (seconds)


class OneToAllFields(BaseSettings):
    """Expected fields in MOTIS one-to-all API response."""

    # Top-level response structure
    one: str = "one"  # Origin location information
    all: str = "all"  # Array of reachable locations
    statistics: str = "statistics"  # Performance/calculation stats

    # Fields within each reachable location
    place: str = "place"  # Place/location object
    lat: str = "lat"
    lon: str = "lon"
    travel_time: str = "duration"  # Travel time to this location (minutes)
    name: str = "name"  # Stop/location name
    stop_id: str = "stopId"  # Stop ID
    arrival: str = "arrival"  # Arrival time
    vertex_type: str = "vertexType"  # Type of vertex (TRANSIT, etc.)

    # Optional route information
    importance: str = "importance"  # Stop importance score
    level: str = "level"  # Level/floor information


class OneToAllDefaults(BaseSettings):
    """Default values for one-to-all API requests based on official MOTIS documentation."""

    max_travel_time: int = 90  # 90 minutes default max travel time
    arrive_by: bool = False  # false = one to all, true = all to one
    min_transfer_time: int = 0  # 0 minutes minimum transfer time
    additional_transfer_time: int = 0  # 0 minutes additional transfer time
    transfer_time_factor: float = 1.0  # 1.0 factor for transfer times
    max_matching_distance: float = 25.0  # 25 meters maximum matching distance
    use_routed_transfers: bool = False  # false = use basic transfers
    pedestrian_profile: str = "FOOT"  # FOOT accessibility profile
    elevation_costs: str = "NONE"  # NONE elevation costs
    require_bike_transport: bool = False  # false = no bike transport requirement
    require_car_transport: bool = False  # false = no car transport requirement
    max_pre_transit_time: int = 900  # 15 minutes (900 seconds) to reach transit
    max_post_transit_time: int = 900  # 15 minutes (900 seconds) from transit
    transit_modes: list = ["TRANSIT"]  # Default all transit modes
    pre_transit_modes: list = ["WALK"]  # Default walking to transit
    post_transit_modes: list = ["WALK"]  # Default walking from transit


# =====================================================================
# THE MAIN SETTINGS OBJECT
# =====================================================================


class MotisSettings(BaseSettings):
    """
    A type-safe, centralized configuration model for the MOTIS API Adapter.
    """

    model_config = SettingsConfigDict(env_nested_delimiter="__")

    request_params: RequestParams = Field(default_factory=RequestParams)
    itinerary_fields: ItineraryFields = Field(default_factory=ItineraryFields)
    leg_fields: LegFields = Field(default_factory=LegFields)
    location_fields: LocationFields = Field(default_factory=LocationFields)
    defaults: Defaults = Field(default_factory=Defaults)
    endpoints: Endpoints = Field(default_factory=Endpoints)

    # One-to-all specific configurations
    one_to_all_params: OneToAllParams = Field(default_factory=OneToAllParams)
    one_to_all_fields: OneToAllFields = Field(default_factory=OneToAllFields)
    one_to_all_defaults: OneToAllDefaults = Field(default_factory=OneToAllDefaults)


# --- Create a single, importable instance of the settings ---
motis_settings = MotisSettings()
