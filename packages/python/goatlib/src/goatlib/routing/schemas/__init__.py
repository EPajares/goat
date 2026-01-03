"""
Routing schemas for goatlib.

This module re-exports catchment area schemas from goatlib.analysis.schemas
for backward compatibility and convenience.
"""

from goatlib.analysis.schemas.catchment_area import (
    AccessEgressMode,
    ActiveMobilityMode,
    ActiveMobilitySettings,
    CarMode,
    CarSettings,
    CatchmentAreaActiveMobilityRequest,
    CatchmentAreaCarRequest,
    CatchmentAreaPolygon,
    CatchmentAreaPTRequest,
    CatchmentAreaResponse,
    CatchmentAreaType,
    Coordinates,
    DecayFunction,
    DecayFunctionType,
    OutputFormat,
    PTMode,
    PTSettings,
    PTTimeWindow,
    RoutingProvider,
    StartingPoints,
    TravelDistanceCost,
    TravelTimeCost,
    TravelTimeCostPT,
)

from .base import Route, TransportMode
