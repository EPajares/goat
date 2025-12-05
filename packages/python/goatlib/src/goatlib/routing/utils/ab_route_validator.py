import logging
from typing import Dict, List, Optional, Tuple

from goatlib.routing.schemas.ab_routing import ABLeg, ABRoute
from goatlib.routing.schemas.base import Location, Mode

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

    def validate_route(self, route: ABRoute) -> List[PlausibilityIssue]:
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

    def _validate_route_duration(self, route: ABRoute) -> List[PlausibilityIssue]:
        """Validate total route duration."""
        issues = []

        if route.duration > self.max_total_duration:
            hours = route.duration / 3600
            issues.append(
                PlausibilityIssue(
                    "warning", f"Route duration very long: {hours:.1f} hours"
                )
            )

        # Check if total duration matches sum of legs, accounting for waiting/transfer times
        leg_duration_sum = sum(leg.duration for leg in route.legs)

        # Calculate expected waiting/transfer time between legs
        total_waiting_time = 0
        for i in range(len(route.legs) - 1):
            current_leg = route.legs[i]
            next_leg = route.legs[i + 1]
            waiting = (
                next_leg.departure_time - current_leg.arrival_time
            ).total_seconds()
            if waiting > 0:
                total_waiting_time += waiting

        # Expected total time = legs + waiting time
        expected_total = leg_duration_sum + total_waiting_time
        expected_diff = abs(route.duration - expected_total)

        # Use a larger tolerance for routes with transfers
        transfer_count = sum(
            1
            for i in range(len(route.legs) - 1)
            if self._is_transit_mode(route.legs[i].mode)
            and self._is_transit_mode(route.legs[i + 1].mode)
        )

        tolerance = 60 + (transfer_count * 120)  # Base 1 min + 2 min per transfer

        if expected_diff > tolerance:
            issues.append(
                PlausibilityIssue(
                    "info",  # Reduced to info since MOTIS may have different calculation
                    f"Route duration ({route.duration:.0f}s) doesn't match legs + waiting ({expected_total:.0f}s)",
                )
            )

        return issues

    def _validate_route_connectivity(self, route: ABRoute) -> List[PlausibilityIssue]:
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

            # Allow small overlaps for realistic transit scenarios
            # Walking to transit can have small overlap as you board before walking "officially ends"
            max_acceptable_overlap = 120  # 2 minutes tolerance

            if time_gap < -max_acceptable_overlap:
                issues.append(
                    PlausibilityIssue(
                        "error",
                        f"Large time overlap: next leg starts {-time_gap:.0f}s before previous ends",
                        i,
                    )
                )
            elif -max_acceptable_overlap <= time_gap < 0:
                # Small overlap is acceptable, especially for walking to transit
                if not (
                    current_leg.mode == Mode.WALK
                    and self._is_transit_mode(next_leg.mode)
                ):
                    issues.append(
                        PlausibilityIssue(
                            "warning",
                            f"Small time overlap: next leg starts {-time_gap:.0f}s before previous ends",
                            i,
                        )
                    )
            elif time_gap > self.max_transfer_time:
                # Check if both legs are transit
                if self._is_transit_mode(current_leg.mode) and self._is_transit_mode(
                    next_leg.mode
                ):
                    issues.append(
                        PlausibilityIssue(
                            "warning",
                            f"Very long transfer time: {time_gap/60:.1f} minutes",
                            i,
                        )
                    )

        return issues

    def _validate_walking_distance(self, route: ABRoute) -> List[PlausibilityIssue]:
        """Validate total walking distance."""
        issues = []

        total_walking = sum(
            leg.distance or 0
            for leg in route.legs
            if leg.mode == Mode.WALK and leg.distance
        )

        if total_walking > self.max_walking_distance:
            km = total_walking / 1000
            issues.append(
                PlausibilityIssue("warning", f"Very long walking distance: {km:.1f}km")
            )

        return issues

    def _validate_leg(self, leg: ABLeg, index: int) -> List[PlausibilityIssue]:
        """Validate individual leg plausibility."""
        issues = []

        # Duration validation
        if leg.duration <= 0:
            issues.append(
                PlausibilityIssue("error", f"Invalid duration: {leg.duration}s", index)
            )

        # Speed validation - only for legs where distance is reliable
        if leg.distance and leg.duration > 0:
            speed = self._calculate_speed_kmh(leg)

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

            # Only check minimum speed for walking/cycling where distance is more reliable
            if (
                not self._is_transit_mode(leg.mode)
                and speed < min_speed
                and leg.distance > 100
            ):
                issues.append(
                    PlausibilityIssue(
                        "warning",
                        f"Speed very low for {leg.mode.value}: {speed:.1f} km/h (min: {min_speed})",
                        index,
                    )
                )

        # Distance validation - simplified approach to avoid MOTIS calculation issues
        if leg.distance and leg.distance > 0:
            # Only flag obviously problematic distances
            if leg.distance > 100000:  # More than 100km for a single leg
                issues.append(
                    PlausibilityIssue(
                        "warning",
                        f"Extremely long leg distance: {leg.distance/1000:.1f}km",
                        index,
                    )
                )

            # For walking legs, we can still do some basic validation since MOTIS provides actual distance
            if leg.mode == Mode.WALK:
                straight_line = self._calculate_distance(leg.origin, leg.destination)
                if straight_line > 0:
                    ratio = leg.distance / straight_line
                    if (
                        ratio > 10
                    ):  # More than 10x straight line for walking is suspicious
                        issues.append(
                            PlausibilityIssue(
                                "warning",
                                f"Walking distance seems excessive: {ratio:.1f}x straight line distance",
                                index,
                            )
                        )
                    elif (
                        ratio < 0.8
                    ):  # Walking shorter than straight line is impossible
                        issues.append(
                            PlausibilityIssue(
                                "error",
                                f"Walking distance shorter than straight line: {ratio:.1f}x",
                                index,
                            )
                        )

        return issues

    def _validate_transfers(self, route: ABRoute) -> List[PlausibilityIssue]:
        """Validate transfer patterns and times."""
        issues = []

        # Find transit legs
        transit_legs = [
            (i, leg)
            for i, leg in enumerate(route.legs)
            if self._is_transit_mode(leg.mode)
        ]

        # Check transfer count
        if len(transit_legs) > 5:
            issues.append(
                PlausibilityIssue(
                    "warning", f"Very many transfers: {len(transit_legs) - 1}"
                )
            )

        # Check transfer times between consecutive transit legs
        for i in range(len(transit_legs) - 1):
            current_idx, current_leg = transit_legs[i]
            next_idx, next_leg = transit_legs[i + 1]

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
            elif transfer_time > self.max_transfer_time:
                issues.append(
                    PlausibilityIssue(
                        "warning",
                        f"Very long transfer: {transfer_time/60:.1f} minutes",
                        current_idx,
                    )
                )

        return issues

    def _is_transit_mode(self, mode: Mode) -> bool:
        """Check if mode is public transit."""
        return mode in [Mode.TRANSIT, Mode.BUS, Mode.TRAM, Mode.RAIL, Mode.SUBWAY]

    def _calculate_speed_kmh(self, leg: ABLeg) -> float:
        """Calculate average speed in km/h for a leg."""
        if leg.duration <= 0 or not leg.distance:
            return 0.0
        return (leg.distance / 1000) / (leg.duration / 3600)

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
        self, route: ABRoute
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

    def print_summary(self) -> None:
        """Print a human-readable summary."""
        summary = self.get_summary()

        print("\n" + "=" * 50)
        print("ROUTE VALIDATION SUMMARY")
        print("=" * 50)
        print(f"Routes validated: {summary['routes_validated']}")
        print(f"Total issues found: {summary['total_issues']}")
        print(f"Average quality score: {summary['average_score']:.1f}/100")
        print()

        print("Issues by severity:")
        for severity, count in summary["issues_by_severity"].items():
            print(f"  {severity.title()}: {count}")
        print()

        if summary["most_common_issues"]:
            print("Most common issues:")
            for issue, count in summary["most_common_issues"]:
                print(f"  {issue}: {count} routes")

        print("=" * 50 + "\n")


def validate_route_response(routes: List[ABRoute]) -> ValidationReport:
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


def validate_single_route(
    route: ABRoute, verbose: bool = True
) -> Tuple[List[PlausibilityIssue], float]:
    """Validate a single route and optionally print results."""
    validator = RouteValidator()
    issues, score = validator.validate_and_score(route)

    if verbose and issues:
        print(f"\nRoute Validation (Score: {score:.1f}/100)")
        print("-" * 30)
        for issue in issues:
            print(f"  {issue}")

    return issues, score
