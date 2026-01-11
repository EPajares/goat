"""Trip Count Station schemas.

Parameters for calculating public transport trip counts per station.
"""

from pathlib import Path

from pydantic import BaseModel, Field

# Import PTTimeWindow from base (canonical location)
from goatlib.analysis.schemas.base import PTTimeWindow

__all__ = [
    "TripCountStationParams",
    "PTTimeWindow",
]


class TripCountStationParams(BaseModel):
    """Parameters for Trip Count Station analysis.

    This tool calculates the number of public transport departures per station
    within a given time window, grouped by transport mode.

    Attributes:
        reference_area_path: Path to polygon layer defining the analysis area.
        stops_path: Path to GTFS stops parquet file.
        stop_times_path: Path to GTFS stop_times parquet file.
        time_window: Time window for the analysis.
        output_path: Path for the output trip count layer.
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
        description="Path for the output trip count layer (parquet format).",
    )
