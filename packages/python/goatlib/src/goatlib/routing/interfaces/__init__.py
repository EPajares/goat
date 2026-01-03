"""
Routing service interfaces.

This module exports abstract interfaces for routing services that can be
implemented by different providers (R5, GOAT Routing, MOTIS, OTP, etc.).
"""

from .catchment_area_service import (
    CatchmentAreaService,
    GoatRoutingService,
    R5Service,
)
from .mocks import (
    MockCatchmentAreaService,
    MockGoatRoutingService,
    MockR5Service,
)
