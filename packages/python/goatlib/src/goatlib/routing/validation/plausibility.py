"""
Plausibility validation for MOTIS routing responses.
This module provides comprehensive validation to ensure MOTIS responses make sense.
"""

import logging
from typing import Dict, List, Optional, Tuple

from goatlib.routing.schemas.ab_routing_enhanced import EnhancedABRoute, EnhancedABLeg
from goatlib.routing.schemas.base import Mode, Location

logger = logging.getLogger(__name__)


class PlausibilityIssue:
    """Represents a plausibility issue found in a route."""

    def __init__(
        self, severity: str, message: str, leg_index: Optional[int] = None
    ) -> None:
        self.severity = severity  # "error", "warning", "info"
        self.message = message
        self.leg_index = leg_index

    def __str__(self) -> str:
        if self.leg_index is not None:
            return f"{self.severity.upper()} [Leg {self.leg_index}]: {self.message}"
        return f"{self.severity.upper()}: {self.message}"


class RouteValidator:
    """Validates route plausibility with configurable thresholds."""

    def __init__(self) -> None:
        # Speed limits in km/h for different modes
        self.max_speeds = {
            Mode.WALK: 8.0,  # Fast walking
            Mode.BIKE: 35.0,  # E-bike or very fast cycling
            Mode.CAR: 120.0,  # Highway speeds
            Mode.BUS: 80.0,  # Urban bus max speed
            Mode.TRAM: 60.0,  # Urban tram max speed
            Mode.RAIL: 200.0,  # High-speed rail
            Mode.SUBWAY: 80.0,  # Metro max speed
            Mode.TRANSIT: 200.0,  # Generic transit (conservative)
        }

        # Minimum speeds in km/h (below which is suspicious)
        self.min_speeds = {
            Mode.WALK: 1.0,  # Very slow walking
            Mode.BIKE: 5.0,  # Very slow cycling
            Mode.CAR: 10.0,  # Traffic jam speeds
            Mode.BUS: 5.0,  # Heavy traffic
            Mode.TRAM: 5.0,  # Heavy traffic
            Mode.RAIL: 20.0,  # Stopping train
            Mode.SUBWAY: 10.0,  # Stopping metro
            Mode.TRANSIT: 5.0,  # Conservative minimum
        }

        # Transfer time limits
        self.min_transfer_time = 60  # seconds
        self.max_transfer_time = 1800  # 30 minutes
        self.max_walking_distance = 5000  # 5km max walking distance
        self.max_total_duration = 8 * 3600  # 8 hours max total trip

    def validate_route(self, route: EnhancedABRoute) -> List[PlausibilityIssue]:
        """Validate a complete route and return list of issues."""
        issues = []

        if not route.legs:
            issues.append(PlausibilityIssue("error", "Route has no legs"))
            return issues

        # Route-level validations
        issues.extend(self._validate_route_duration(route))
        issues.extend(self._validate_route_connectivity(route))
        issues.extend(self._validate_walking_distance(route))

        # Leg-level validations
        for i, leg in enumerate(route.legs):
            issues.extend(self._validate_leg(leg, i))

        # Transfer validations
        issues.extend(self._validate_transfers(route))

        return issues

    def _validate_route_duration(
        self, route: EnhancedABRoute
    ) -> List[PlausibilityIssue]:
        """Validate total route duration."""
        issues = []

        if route.duration > self.max_total_duration:
            hours = route.duration / 3600
            issues.append(
                PlausibilityIssue(
                    "warning", f"Route duration very long: {hours:.1f} hours"
                )
            )

        # Check if total duration matches sum of legs
        leg_duration_sum = sum(leg.duration for leg in route.legs)
        if abs(route.duration - leg_duration_sum) > 60:  # 1 minute tolerance
            issues.append(
                PlausibilityIssue(
                    "warning",
                    f"Route duration ({route.duration:.0f}s) doesn't match sum of legs ({leg_duration_sum:.0f}s)",
                )
            )

        return issues

    def _validate_route_connectivity(
        self, route: EnhancedABRoute
    ) -> List[PlausibilityIssue]:
        """Validate that legs connect properly."""
        issues = []

        for i in range(len(route.legs) - 1):
            current_leg = route.legs[i]
            next_leg = route.legs[i + 1]

            # Check location connectivity
            distance = self._calculate_distance(
                current_leg.destination, next_leg.origin
            )

            if distance > 1000:  # 1km tolerance for connections
                issues.append(
                    PlausibilityIssue(
                        "error", f"Large gap between legs: {distance:.0f}m", i
                    )
                )

            # Check time connectivity
            time_gap = (
                next_leg.departure_time - current_leg.arrival_time
            ).total_seconds()

            if time_gap < 0:
                issues.append(
                    PlausibilityIssue(
                        "error",
                        f"Time overlap: next leg starts {-time_gap:.0f}s before previous ends",
                        i,
                    )
                )
            elif (
                time_gap > self.max_transfer_time
                and current_leg.is_transit
                and next_leg.is_transit
            ):
                issues.append(
                    PlausibilityIssue(
                        "warning",
                        f"Very long transfer time: {time_gap/60:.1f} minutes",
                        i,
                    )
                )

        return issues

    def _validate_walking_distance(
        self, route: EnhancedABRoute
    ) -> List[PlausibilityIssue]:
        """Validate total walking distance."""
        issues = []

        if route.walking_distance > self.max_walking_distance:
            km = route.walking_distance / 1000
            issues.append(
                PlausibilityIssue("warning", f"Very long walking distance: {km:.1f}km")
            )

        return issues

    def _validate_leg(self, leg: EnhancedABLeg, index: int) -> List[PlausibilityIssue]:
        """Validate individual leg plausibility."""
        issues = []

        # Duration validation
        if leg.duration <= 0:
            issues.append(
                PlausibilityIssue("error", f"Invalid duration: {leg.duration}s", index)
            )

        # Speed validation
        if leg.distance and leg.duration > 0:
            speed = leg.speed_kmh

            max_speed = self.max_speeds.get(leg.mode, 200.0)
            min_speed = self.min_speeds.get(leg.mode, 0.1)

            if speed > max_speed:
                issues.append(
                    PlausibilityIssue(
                        "error",
                        f"Speed too high for {leg.mode.value}: {speed:.1f} km/h (max: {max_speed})",
                        index,
                    )
                )

            if (
                speed < min_speed and leg.distance > 100
            ):  # Only check for meaningful distances
                issues.append(
                    PlausibilityIssue(
                        "warning",
                        f"Speed very low for {leg.mode.value}: {speed:.1f} km/h (min: {min_speed})",
                        index,
                    )
                )

        # Transit-specific validations
        if leg.is_transit:
            issues.extend(self._validate_transit_leg(leg, index))

        return issues

    def _validate_transit_leg(
        self, leg: EnhancedABLeg, index: int
    ) -> List[PlausibilityIssue]:
        """Validate transit-specific aspects of a leg."""
        issues = []

        # Check for transit info
        if not leg.transit_info:
            issues.append(
                PlausibilityIssue(
                    "warning", "Transit leg missing line information", index
                )
            )
        else:
            # Validate transit info completeness
            if (
                not leg.transit_info.route_short_name
                and not leg.transit_info.route_long_name
            ):
                issues.append(
                    PlausibilityIssue("info", "Transit leg missing route name", index)
                )

            if not leg.transit_info.agency_name:
                issues.append(
                    PlausibilityIssue(
                        "info", "Transit leg missing agency information", index
                    )
                )

        # Check stop information
        if not leg.origin_stop or not leg.destination_stop:
            issues.append(
                PlausibilityIssue("info", "Transit leg missing stop information", index)
            )

        return issues

    def _validate_transfers(self, route: EnhancedABRoute) -> List[PlausibilityIssue]:
        """Validate transfer patterns and times."""
        issues = []

        transit_legs = [i for i, leg in enumerate(route.legs) if leg.is_transit]

        # Check transfer count
        if len(transit_legs) > 5:
            issues.append(
                PlausibilityIssue(
                    "warning", f"Very many transfers: {len(transit_legs) - 1}"
                )
            )

        # Check transfer times
        for i in range(len(transit_legs) - 1):
            current_idx = transit_legs[i]
            next_idx = transit_legs[i + 1]

            current_leg = route.legs[current_idx]
            next_leg = route.legs[next_idx]

            # Calculate transfer time (including any walking legs in between)
            transfer_start = current_leg.arrival_time
            transfer_end = next_leg.departure_time
            transfer_time = (transfer_end - transfer_start).total_seconds()

            if transfer_time < self.min_transfer_time:
                issues.append(
                    PlausibilityIssue(
                        "warning",
                        f"Very short transfer: {transfer_time:.0f}s",
                        current_idx,
                    )
                )

        return issues

    def _calculate_distance(self, loc1: Location, loc2: Location) -> float:
        """Calculate distance between two locations in meters (Haversine)."""
        import math

        # Convert to radians
        lat1, lon1 = math.radians(loc1.lat), math.radians(loc1.lon)
        lat2, lon2 = math.radians(loc2.lat), math.radians(loc2.lon)

        # Haversine formula
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = (
            math.sin(dlat / 2) ** 2
            + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
        )
        c = 2 * math.asin(math.sqrt(a))
        r = 6371000  # Earth radius in meters

        return r * c

    def validate_and_score(
        self, route: EnhancedABRoute
    ) -> Tuple[List[PlausibilityIssue], float]:
        """Validate route and return a plausibility score (0-100, higher is better)."""
        issues = self.validate_route(route)

        # Calculate score based on issues
        score = 100.0
        for issue in issues:
            if issue.severity == "error":
                score -= 25.0
            elif issue.severity == "warning":
                score -= 10.0
            elif issue.severity == "info":
                score -= 2.0

        return issues, max(0.0, min(100.0, score))


class ValidationReport:
    """Report summarizing validation results across multiple routes."""

    def __init__(self) -> None:
        self.routes_validated = 0
        self.total_issues = 0
        self.issues_by_severity = {"error": 0, "warning": 0, "info": 0}
        self.common_issues: Dict[str, int] = {}
        self.scores: List[float] = []

    def add_route_validation(
        self, route_issues: List[PlausibilityIssue], score: float
    ) -> None:
        """Add validation results for a single route."""
        self.routes_validated += 1
        self.total_issues += len(route_issues)
        self.scores.append(score)

        for issue in route_issues:
            self.issues_by_severity[issue.severity] += 1

            # Track common issue patterns
            issue_key = issue.message.split(":")[0]  # Use first part as key
            self.common_issues[issue_key] = self.common_issues.get(issue_key, 0) + 1

    def get_summary(self) -> Dict:
        """Get summary statistics."""
        avg_score = sum(self.scores) / len(self.scores) if self.scores else 0

        return {
            "routes_validated": self.routes_validated,
            "total_issues": self.total_issues,
            "average_score": avg_score,
            "issues_by_severity": self.issues_by_severity,
            "most_common_issues": sorted(
                self.common_issues.items(), key=lambda x: x[1], reverse=True
            )[:5],
            "score_distribution": {
                "min": min(self.scores) if self.scores else 0,
                "max": max(self.scores) if self.scores else 0,
                "avg": avg_score,
            },
        }


def validate_route_response(routes: List[EnhancedABRoute]) -> ValidationReport:
    """Validate a list of routes and return comprehensive report."""
    validator = RouteValidator()
    report = ValidationReport()

    for route in routes:
        issues, score = validator.validate_and_score(route)
        report.add_route_validation(issues, score)

        # Log significant issues
        for issue in issues:
            if issue.severity == "error":
                logger.error(f"Route validation: {issue}")
            elif issue.severity == "warning":
                logger.warning(f"Route validation: {issue}")

    return report
