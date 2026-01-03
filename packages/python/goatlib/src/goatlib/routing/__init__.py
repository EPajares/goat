"""
Goatlib Routing Module.

This module provides routing interfaces for catchment area
calculations using multiple routing providers (R5, GOAT Routing, MOTIS, OTP).

Usage:
    from goatlib.routing import CatchmentAreaService, MockCatchmentAreaService
"""

from .interfaces import (
    CatchmentAreaService,
    GoatRoutingService,
    MockCatchmentAreaService,
    MockGoatRoutingService,
    MockR5Service,
    R5Service,
)
