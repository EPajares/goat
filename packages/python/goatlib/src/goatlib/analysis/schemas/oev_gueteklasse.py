"""ÖV-Güteklassen (Public Transport Quality Classes) schemas.

This module contains parameter schemas for the ÖV-Güteklassen tool based on
the Swiss ARE methodology for calculating public transport quality classes.

Reference:
    Bundesamt für Raumentwicklung ARE, 2022.
    ÖV-Güteklassen Berechnungsmethodik ARE (Grundlagenbericht).
"""

from enum import Enum
from pathlib import Path

from pydantic import BaseModel, Field, field_validator


class CatchmentType(str, Enum):
    """Catchment area type for ÖV-Güteklassen."""

    buffer = "buffer"


class OevGueteklasseStationConfig(BaseModel):
    """Station configuration for ÖV-Güteklassen classification.

    This defines how different transport modes are grouped and how
    service frequency translates to station categories.

    Attributes:
        groups: Mapping of GTFS route_type to transport group (A, B, C).
            Group A: Rail, S-Bahn, Metro (highest priority)
            Group B: Tram, Light Rail
            Group C: Bus (lowest priority)
        time_frequency: Frequency thresholds in minutes [5, 10, 20, 40, 60, 120].
            If average service interval is < 5min -> time_interval=1
            If average service interval is 5-10min -> time_interval=2, etc.
        categories: List of dicts mapping group+time_interval to station category.
            E.g., categories[0] = {"A": 1, "B": 1, "C": 2} means:
            - Group A with time_interval 1 -> Station Category I
            - Group B with time_interval 1 -> Station Category I
            - Group C with time_interval 1 -> Station Category II
        classification: Maps station category to buffer distances and quality classes.
            E.g., classification["1"] = {300: "1", 500: "1", 750: "2", 1000: "3"}
            means Station Category I gets:
            - 300m buffer -> Quality Class 1 (A)
            - 500m buffer -> Quality Class 1 (A)
            - 750m buffer -> Quality Class 2 (B)
            - 1000m buffer -> Quality Class 3 (C)
    """

    groups: dict[str, str] = Field(
        ...,
        description="Mapping of GTFS route_type to transport group (A, B, or C).",
    )
    time_frequency: list[int] = Field(
        ...,
        description="Frequency thresholds in minutes.",
    )
    categories: list[dict[str, int]] = Field(
        ...,
        description="Mapping of group+frequency index to station category.",
    )
    classification: dict[str, dict[int, str]] = Field(
        ...,
        description="Maps station category to buffer distances and quality classes.",
    )

    @field_validator("classification", mode="before")
    @classmethod
    def convert_classification_keys_to_int(cls, v: dict) -> dict[str, dict[int, str]]:
        """Convert string distance keys to integers for API compatibility."""
        return {
            cat: {int(dist): qclass for dist, qclass in distances.items()}
            for cat, distances in v.items()
        }


class PTTimeWindow(BaseModel):
    """Public transport time window for analysis.

    Attributes:
        weekday: Type of day - "weekday", "saturday", or "sunday"
        from_time: Start time in seconds from midnight (e.g., 25200 = 7:00)
        to_time: End time in seconds from midnight (e.g., 32400 = 9:00)
    """

    weekday: str = Field(
        ...,
        description="Type of day: 'weekday', 'saturday', or 'sunday'",
    )
    from_time: int = Field(
        ...,
        description="Start time in seconds from midnight",
    )
    to_time: int = Field(
        ...,
        description="End time in seconds from midnight",
    )

    @property
    def weekday_column(self) -> str:
        """Get the boolean column name for the weekday type."""
        mapping = {
            "weekday": "is_weekday",
            "saturday": "is_saturday",
            "sunday": "is_sunday",
        }
        return mapping.get(self.weekday, "is_weekday")

    @property
    def from_time_str(self) -> str:
        """Convert from_time to HH:MM:SS format."""
        hours = self.from_time // 3600
        minutes = (self.from_time % 3600) // 60
        seconds = self.from_time % 60
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

    @property
    def to_time_str(self) -> str:
        """Convert to_time to HH:MM:SS format."""
        hours = self.to_time // 3600
        minutes = (self.to_time % 3600) // 60
        seconds = self.to_time % 60
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

    @property
    def time_window_minutes(self) -> float:
        """Get the time window duration in minutes."""
        return (self.to_time - self.from_time) / 60


# Default station configuration based on Swiss ARE methodology
# Extended route types: https://developers.google.com/transit/gtfs/reference/extended-route-types
STATION_CONFIG_DEFAULT = OevGueteklasseStationConfig(
    groups={
        # Standard GTFS route types
        "0": "B",  # Tram, Streetcar
        "1": "A",  # Subway, Metro
        "2": "A",  # Rail
        "3": "C",  # Bus
        "7": "B",  # Funicular
        # Extended route types - Rail
        "100": "A",  # Railway Service
        "101": "A",  # High Speed Rail
        "102": "A",  # Long Distance Trains
        "103": "A",  # Inter Regional Rail
        "104": "A",  # Car Transport Rail
        "105": "A",  # Sleeper Rail
        "106": "A",  # Regional Rail
        "107": "A",  # Tourist Railway
        "108": "A",  # Rail Shuttle
        "109": "A",  # Suburban Railway (S-Bahn)
        "110": "A",  # Replacement Rail
        "111": "A",  # Special Rail
        "112": "A",  # Lorry Transport Rail
        "114": "A",  # All Rails
        "116": "A",  # Cross-Country Rail
        "117": "A",  # Vehicle Transport Rail
        # Extended route types - Coach
        "200": "C",  # Coach Service
        "201": "C",  # International Coach
        "202": "C",  # National Coach
        "204": "C",  # Regional Coach
        # Extended route types - Urban Rail
        "400": "A",  # Urban Railway
        "401": "A",  # Metro
        "402": "A",  # Underground
        "403": "A",  # Urban Rail
        "405": "A",  # Monorail
        # Extended route types - Bus
        "700": "C",  # Bus Service
        "701": "C",  # Regional Bus
        "702": "C",  # Express Bus
        "704": "C",  # Local Bus
        "705": "C",  # Night Bus
        "712": "C",  # School Bus
        "715": "C",  # Demand Responsive Bus
        "800": "C",  # Trolleybus
        # Extended route types - Tram
        "900": "B",  # Tram Service
        "901": "B",  # City Tram
        "902": "B",  # Local Tram
        "903": "B",  # Regional Tram
        "904": "B",  # Sightseeing Tram
        "905": "B",  # Shuttle Tram
        "906": "B",  # All Trams
        # Extended route types - Water/Cable/Other
        "1000": "C",  # Water Transport
        "1300": "C",  # Aerial Lift
        "1400": "B",  # Funicular
    },
    time_frequency=[5, 10, 20, 40, 60, 120],
    categories=[
        {"A": 1, "B": 1, "C": 2},  # Frequency interval 1 (< 5 min)
        {"A": 1, "B": 2, "C": 3},  # Frequency interval 2 (5-10 min)
        {"A": 2, "B": 3, "C": 4},  # Frequency interval 3 (10-20 min)
        {"A": 3, "B": 4, "C": 5},  # Frequency interval 4 (20-40 min)
        {"A": 4, "B": 5, "C": 6},  # Frequency interval 5 (40-60 min)
        {"A": 5, "B": 6, "C": 7},  # Frequency interval 6 (60-120 min)
    ],
    classification={
        "1": {300: "1", 500: "1", 750: "2", 1000: "3"},
        "2": {300: "1", 500: "2", 750: "3", 1000: "4"},
        "3": {300: "2", 500: "3", 750: "4", 1000: "5"},
        "4": {300: "3", 500: "4", 750: "5", 1000: "6"},
        "5": {300: "4", 500: "5", 750: "6"},
        "6": {300: "5", 500: "6"},
        "7": {300: "6"},
    },
)


class OevGueteklasseParams(BaseModel):
    """Parameters for ÖV-Güteklassen analysis.

    Attributes:
        reference_area_path: Path to polygon layer defining the analysis area.
        stops_path: Path to GTFS stops parquet file.
        stop_times_path: Path to GTFS stop_times parquet file.
        time_window: Time window for the analysis.
        output_path: Path for the output quality classes layer.
        station_config: Optional custom station configuration.
        stations_output_path: Optional path to save station categories.
    """

    reference_area_path: str | Path = Field(
        ...,
        description="Path to polygon layer defining the analysis area.",
    )
    stops_path: str | Path = Field(
        ...,
        description="Path to GTFS stops parquet file.",
    )
    stop_times_path: str | Path = Field(
        ...,
        description="Path to GTFS stop_times parquet file.",
    )
    time_window: PTTimeWindow = Field(
        ...,
        description="Time window for the analysis.",
    )
    output_path: str | Path = Field(
        ...,
        description="Path for the output quality classes layer.",
    )
    station_config: OevGueteklasseStationConfig | None = Field(
        default=None,
        description="Optional custom station configuration. Defaults to Swiss ARE methodology.",
    )
    stations_output_path: str | Path | None = Field(
        default=None,
        description="Optional path to save station categories.",
    )
