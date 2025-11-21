import asyncio
import json
import time
import tracemalloc
from datetime import datetime
from pathlib import Path
from typing import Dict, Any

import psutil
import pytest
from goatlib.routing.adapters.motis import create_motis_adapter
from goatlib.routing.schemas.ab_routing import ABRoutingRequest, ABRoutingResponse
from goatlib.routing.schemas.base import Location, Mode


class ABRoutingPerformanceMetrics:
    """Class to track AB routing performance metrics during test execution."""

    def __init__(self: "ABRoutingPerformanceMetrics") -> None:
        self.reset()

    def reset(self: "ABRoutingPerformanceMetrics") -> None:
        """Reset all metrics."""
        self.timings = {}
        self.memory_usage = {}
        self.network_stats = {}
        self.response_stats = {}
        self.validation_stats = {}

    def start_timing(self: "ABRoutingPerformanceMetrics", phase: str) -> None:
        """Start timing a specific phase."""
        self.timings[f"{phase}_start"] = time.perf_counter()

    def end_timing(self: "ABRoutingPerformanceMetrics", phase: str) -> None:
        """End timing a specific phase and calculate duration."""
        end_time = time.perf_counter()
        start_time = self.timings.get(f"{phase}_start", end_time)
        self.timings[f"{phase}_duration"] = end_time - start_time

    def record_memory(self: "ABRoutingPerformanceMetrics", phase: str) -> None:
        """Record memory usage at a specific phase."""
        current, peak = tracemalloc.get_traced_memory()
        self.memory_usage[phase] = {
            "current_mb": current / 1024 / 1024,
            "peak_mb": peak / 1024 / 1024,
            "process_rss_mb": psutil.Process().memory_info().rss / 1024 / 1024,
        }

    def record_response_stats(
        self: "ABRoutingPerformanceMetrics",
        response: ABRoutingResponse,
        request: ABRoutingRequest,
    ) -> None:
        """Record AB routing response statistics."""
        route_count = len(response.routes)
        total_legs = sum(len(route.legs) for route in response.routes)
        total_distance = sum(route.distance or 0 for route in response.routes)
        total_duration = sum(route.duration for route in response.routes)

        # Analyze route complexity
        modes_used = set()
        transfer_count = 0
        walking_legs = 0
        transit_legs = 0

        for route in response.routes:
            for leg in route.legs:
                modes_used.add(leg.mode.value)
                if leg.mode == Mode.WALK:
                    walking_legs += 1
                else:
                    transit_legs += 1
            # Count transfers (transitions between transit modes)
            transit_modes_in_route = [
                leg.mode for leg in route.legs if leg.mode != Mode.WALK
            ]
            if len(transit_modes_in_route) > 1:
                transfer_count += len(transit_modes_in_route) - 1

        self.response_stats = {
            "route_count": route_count,
            "total_legs": total_legs,
            "total_distance_m": total_distance,
            "total_duration_s": total_duration,
            "modes_used": list(modes_used),
            "mode_count": len(modes_used),
            "transfer_count": transfer_count,
            "walking_legs": walking_legs,
            "transit_legs": transit_legs,
            "avg_route_distance": total_distance / route_count
            if route_count > 0
            else 0,
            "avg_route_duration": total_duration / route_count
            if route_count > 0
            else 0,
            "max_results_requested": request.max_results,
            "transport_modes_requested": [mode.value for mode in request.modes],
        }

    def record_validation_stats(
        self: "ABRoutingPerformanceMetrics", response: ABRoutingResponse
    ) -> None:
        """Record comprehensive plausibility validation statistics."""
        from goatlib.routing.validation.route_plausibility import (
            validate_route_response,
        )

        # Run plausibility validation
        validation_report = validate_route_response(response.routes)
        summary = validation_report.get_summary()

        # Basic validation
        valid_routes = 0
        route_errors = []
        leg_errors = []

        for i, route in enumerate(response.routes):
            route_valid = True

            # Validate route properties
            if route.duration <= 0:
                route_errors.append(f"Route {i}: Invalid duration {route.duration}")
                route_valid = False

            if route.distance is not None and route.distance < 0:
                route_errors.append(f"Route {i}: Negative distance {route.distance}")
                route_valid = False

            # Validate legs
            for j, leg in enumerate(route.legs):
                if leg.duration <= 0:
                    leg_errors.append(
                        f"Route {i} Leg {j}: Invalid duration {leg.duration}"
                    )
                    route_valid = False

                if leg.distance is not None and leg.distance < 0:
                    leg_errors.append(
                        f"Route {i} Leg {j}: Negative distance {leg.distance}"
                    )
                    route_valid = False

                if leg.arrival_time <= leg.departure_time:
                    leg_errors.append(f"Route {i} Leg {j}: Invalid timing")
                    route_valid = False

            if route_valid:
                valid_routes += 1

        self.validation_stats = {
            "valid_routes": valid_routes,
            "total_routes": len(response.routes),
            "validation_success_rate": valid_routes / len(response.routes)
            if response.routes
            else 0,
            "route_errors": route_errors,
            "leg_errors": leg_errors,
            "error_count": len(route_errors) + len(leg_errors),
            # Enhanced plausibility validation
            "plausibility": {
                "average_score": summary["average_score"],
                "issues_by_severity": summary["issues_by_severity"],
                "total_issues": summary["total_issues"],
                "most_common_issues": summary["most_common_issues"],
                "score_distribution": summary["score_distribution"],
            },
        }

    def to_dict(self) -> Dict[str, Any]:
        """Convert metrics to dictionary."""
        return {
            "timings": self.timings,
            "memory_usage": self.memory_usage,
            "network_stats": self.network_stats,
            "response_stats": self.response_stats,
            "validation_stats": self.validation_stats,
            "timestamp": datetime.now().isoformat(),
        }


def save_ab_routing_benchmark_results(
    metrics: ABRoutingPerformanceMetrics, test_name: str
) -> Path:
    """Save AB routing benchmark results to JSON file."""
    benchmark_dir = Path(__file__).parent / "results"
    benchmark_dir.mkdir(exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{test_name}_{timestamp}.json"
    filepath = benchmark_dir / filename

    with open(filepath, "w") as f:
        json.dump(metrics.to_dict(), f, indent=2)

    print(f"\n📊 AB Routing benchmark results saved to: {filepath}")
    return filepath


def validate_ab_routing_response(response: ABRoutingResponse) -> None:
    """Helper function to validate AB routing response structure."""
    assert response is not None, "Response should not be None"
    assert hasattr(response, "routes"), "Response should have routes attribute"
    assert isinstance(response.routes, list), "Routes should be a list"

    for i, route in enumerate(response.routes):
        assert route.duration > 0, f"Route {i} should have positive duration"
        assert (
            route.distance is None or route.distance >= 0
        ), f"Route {i} should have non-negative distance"
        assert len(route.legs) > 0, f"Route {i} should have at least one leg"

        for j, leg in enumerate(route.legs):
            assert leg.duration > 0, f"Route {i} leg {j} should have positive duration"
            assert (
                leg.distance is None or leg.distance >= 0
            ), f"Route {i} leg {j} should have non-negative distance"
            assert (
                leg.arrival_time > leg.departure_time
            ), f"Route {i} leg {j} should have valid timing"
            assert leg.origin is not None, f"Route {i} leg {j} should have origin"
            assert (
                leg.destination is not None
            ), f"Route {i} leg {j} should have destination"


@pytest.mark.slow
@pytest.mark.network
@pytest.mark.benchmark
async def test_motis_ab_routing_performance_benchmark():
    """
    Comprehensive performance benchmark for MOTIS AB routing functionality.

    Measures:
    - Pre-request preparation time
    - Network request time
    - Post-processing time
    - Memory allocation
    - Response data analysis
    - Route validation performance
    """
    metrics = ABRoutingPerformanceMetrics()

    # Start memory tracing
    tracemalloc.start()

    try:
        # === PRE-REQUEST PHASE ===
        metrics.start_timing("pre_request")
        metrics.record_memory("pre_request_start")

        # Create adapter
        adapter = create_motis_adapter(use_fixtures=False)

        # Create comprehensive routing request (Munich to Stuttgart - major city pair)
        request = ABRoutingRequest(
            origin=Location(lat=48.1351, lon=11.5820),  # Munich central station
            destination=Location(lat=48.7758, lon=9.1829),  # Stuttgart central station
            modes=[Mode.TRANSIT, Mode.WALK],  # Allow transfers and walking
            max_results=5,  # Request multiple alternatives
            max_transfers=3,  # Allow up to 3 transfers for complex routes
            max_walking_distance=1000,  # 1km max walking distance
        )

        metrics.record_memory("pre_request_end")
        metrics.end_timing("pre_request")

        # === REQUEST PHASE ===
        metrics.start_timing("request")
        metrics.record_memory("request_start")

        # Get network stats before request
        net_io_before = psutil.net_io_counters()

        # Execute the actual AB routing request
        response = await adapter.route(request)

        # Get network stats after request
        net_io_after = psutil.net_io_counters()

        metrics.record_memory("request_end")
        metrics.end_timing("request")

        # Calculate network usage
        if net_io_before and net_io_after:
            metrics.network_stats = {
                "bytes_sent": net_io_after.bytes_sent - net_io_before.bytes_sent,
                "bytes_received": net_io_after.bytes_recv - net_io_before.bytes_recv,
                "packets_sent": net_io_after.packets_sent - net_io_before.packets_sent,
                "packets_received": net_io_after.packets_recv
                - net_io_before.packets_recv,
            }

        # === POST-PROCESSING PHASE ===
        metrics.start_timing("post_processing")
        metrics.record_memory("post_processing_start")

        # Validate response structure (simulating typical post-processing)
        validate_ab_routing_response(response)

        # Detailed route analysis (typical use case processing)
        for route in response.routes:
            # Analyze route characteristics
            transit_legs = [leg for leg in route.legs if leg.mode != Mode.WALK]
            walking_legs = [leg for leg in route.legs if leg.mode == Mode.WALK]

            # Validate route connectivity
            for i in range(len(route.legs) - 1):
                current_leg = route.legs[i]
                next_leg = route.legs[i + 1]
                # Ensure legs are connected (destinations match origins)
                assert abs(current_leg.destination.lat - next_leg.origin.lat) < 0.01
                assert abs(current_leg.destination.lon - next_leg.origin.lon) < 0.01

        metrics.record_memory("post_processing_end")
        metrics.end_timing("post_processing")

        # === VALIDATION PHASE ===
        metrics.start_timing("validation")
        metrics.record_response_stats(response, request)
        metrics.record_validation_stats(response)
        metrics.end_timing("validation")

        # === SAVE RESULTS ===
        filepath = save_ab_routing_benchmark_results(
            metrics, "motis_ab_routing_performance"
        )

        # === PRINT DETAILED SUMMARY ===
        print("\n🚀 MOTIS AB Routing Performance Benchmark Results:")
        print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

        print("\n⏱️  Timing Breakdown:")
        print(
            f"   Pre-request:     {metrics.timings.get('pre_request_duration', 0):.3f}s"
        )
        print(f"   Request:         {metrics.timings.get('request_duration', 0):.3f}s")
        print(
            f"   Post-processing: {metrics.timings.get('post_processing_duration', 0):.3f}s"
        )
        print(
            f"   Validation:      {metrics.timings.get('validation_duration', 0):.3f}s"
        )
        total_time = sum(
            v for k, v in metrics.timings.items() if k.endswith("_duration")
        )
        print(f"   Total:           {total_time:.3f}s")

        print("\n💾 Memory Usage:")
        for phase, mem in metrics.memory_usage.items():
            print(
                f"   {phase:18}: Current {mem['current_mb']:.1f}MB, Peak {mem['peak_mb']:.1f}MB, Process RSS {mem['process_rss_mb']:.1f}MB"
            )

        print("\n🌐 Network Stats:")
        net = metrics.network_stats
        total_bandwidth = net.get("bytes_sent", 0) + net.get("bytes_received", 0)
        print(f"   Bytes sent:      {net.get('bytes_sent', 0):,}")
        print(f"   Bytes received:  {net.get('bytes_received', 0):,}")
        print(f"   Total bandwidth: {total_bandwidth / 1024:.1f} KB")
        print(f"   Packets sent:    {net.get('packets_sent', 0):,}")
        print(f"   Packets received:{net.get('packets_received', 0):,}")

        print("\n📊 Route Analysis:")
        stats = metrics.response_stats
        print(
            f"   Routes returned: {stats['route_count']}/{stats['max_results_requested']}"
        )
        print(f"   Total legs:      {stats['total_legs']}")
        print(f"   Transport modes: {', '.join(stats['modes_used'])}")
        print(f"   Transfers:       {stats['transfer_count']}")
        print(f"   Walking legs:    {stats['walking_legs']}")
        print(f"   Transit legs:    {stats['transit_legs']}")

        print("\n📏 Distance & Duration:")
        print(f"   Total distance:  {stats['total_distance_m'] / 1000:.1f} km")
        print(f"   Total duration:  {stats['total_duration_s'] / 60:.1f} min")
        print(f"   Avg route dist:  {stats['avg_route_distance'] / 1000:.1f} km")
        print(f"   Avg route time:  {stats['avg_route_duration'] / 60:.1f} min")

        print("\n✅ Validation Results:")
        val = metrics.validation_stats
        print(f"   Valid routes:    {val['valid_routes']}/{val['total_routes']}")
        print(f"   Success rate:    {val['validation_success_rate']:.1%}")
        print(f"   Errors found:    {val['error_count']}")

        # Performance quality assessment
        quality_score = "EXCELLENT"
        if total_time > 10.0:
            quality_score = "POOR"
        elif total_time > 5.0:
            quality_score = "FAIR"
        elif total_time > 2.0:
            quality_score = "GOOD"

        print(f"\n🎯 Performance Assessment: {quality_score}")
        print(f"   Response time:   {total_time:.3f}s")
        print(
            f"   Memory efficiency: {metrics.memory_usage['request_end']['peak_mb']:.1f}MB peak"
        )
        print(f"   Network efficiency: {total_bandwidth / 1024:.1f}KB bandwidth")
        print(f"   Route quality:   {val['validation_success_rate']:.1%} valid")

        # Performance assertions
        assert total_time < 30.0, f"AB routing took too long: {total_time:.3f}s"
        assert stats["route_count"] > 0, "No routes returned"
        assert (
            val["validation_success_rate"] >= 0.8
        ), f"Too many validation errors: {val['validation_success_rate']:.1%}"
        assert stats["total_distance_m"] > 1000, "Routes seem unrealistically short"

    finally:
        # Cleanup
        if "adapter" in locals():
            await adapter.motis_client.close()
        tracemalloc.stop()


@pytest.mark.slow
@pytest.mark.network
@pytest.mark.benchmark
async def test_motis_ab_routing_minimal_benchmark():
    """
    Minimal benchmark for quick AB routing performance checks.
    Tests short-distance urban routing scenario.
    """
    metrics = ABRoutingPerformanceMetrics()
    tracemalloc.start()

    try:
        # Simple short-distance request for baseline performance
        metrics.start_timing("total")

        adapter = create_motis_adapter(use_fixtures=False)

        # Berlin local routing (Alexanderplatz to Brandenburg Gate)
        request = ABRoutingRequest(
            origin=Location(lat=52.5219, lon=13.4132),  # Alexanderplatz
            destination=Location(lat=52.5163, lon=13.3777),  # Brandenburg Gate
            modes=[Mode.TRANSIT, Mode.WALK],
            max_results=2,  # Minimal results for fast response
            max_transfers=1,  # Single transfer max
        )

        response = await adapter.route(request)

        metrics.end_timing("total")
        metrics.record_memory("final")
        metrics.record_response_stats(response, request)
        metrics.record_validation_stats(response)

        # Save minimal results
        save_ab_routing_benchmark_results(metrics, "motis_ab_routing_minimal")

        print("\n⚡ Minimal AB Routing Benchmark:")
        print(f"   Total time:      {metrics.timings.get('total_duration', 0):.3f}s")
        print(f"   Routes found:    {metrics.response_stats['route_count']}")
        print(f"   Total legs:      {metrics.response_stats['total_legs']}")
        print(f"   Memory peak:     {metrics.memory_usage['final']['peak_mb']:.1f}MB")
        print(
            f"   Success rate:    {metrics.validation_stats['validation_success_rate']:.1%}"
        )

        # Quick assertions
        assert (
            metrics.timings.get("total_duration", 0) < 10.0
        ), "Minimal request too slow"
        assert (
            metrics.response_stats["route_count"] > 0
        ), "Should return at least one route"
        assert (
            metrics.validation_stats["validation_success_rate"] >= 0.8
        ), "Too many validation errors"

    finally:
        if "adapter" in locals():
            await adapter.motis_client.close()
        tracemalloc.stop()


@pytest.mark.slow
@pytest.mark.network
@pytest.mark.benchmark
async def test_motis_ab_routing_stress_benchmark():
    """
    Stress test benchmark for AB routing with challenging parameters.
    Tests maximum complexity routing scenario.
    """
    metrics = ABRoutingPerformanceMetrics()
    tracemalloc.start()

    try:
        # Complex long-distance request with many options
        metrics.start_timing("total")

        adapter = create_motis_adapter(use_fixtures=False)

        # Long-distance routing with maximum complexity (Berlin to Munich)
        request = ABRoutingRequest(
            origin=Location(lat=52.5200, lon=13.4050),  # Berlin
            destination=Location(lat=48.1351, lon=11.5820),  # Munich
            modes=[Mode.TRANSIT, Mode.WALK],
            max_results=10,  # Maximum results
            max_transfers=5,  # Allow many transfers
            max_walking_distance=2000,  # Longer walking distance
        )

        response = await adapter.route(request)

        metrics.end_timing("total")
        metrics.record_memory("final")
        metrics.record_response_stats(response, request)
        metrics.record_validation_stats(response)

        # Save stress test results
        save_ab_routing_benchmark_results(metrics, "motis_ab_routing_stress")

        print("\n🔥 Stress Test AB Routing Benchmark:")
        print(f"   Total time:      {metrics.timings.get('total_duration', 0):.3f}s")
        print(
            f"   Routes found:    {metrics.response_stats['route_count']}/{request.max_results}"
        )
        print(
            f"   Total distance:  {metrics.response_stats['total_distance_m'] / 1000:.1f} km"
        )
        print(f"   Total legs:      {metrics.response_stats['total_legs']}")
        print(f"   Transfers:       {metrics.response_stats['transfer_count']}")
        print(f"   Memory peak:     {metrics.memory_usage['final']['peak_mb']:.1f}MB")
        print(
            f"   Success rate:    {metrics.validation_stats['validation_success_rate']:.1%}"
        )

        # Stress test assertions (more lenient timing)
        assert (
            metrics.timings.get("total_duration", 0) < 60.0
        ), "Stress test took too long"
        assert (
            metrics.response_stats["route_count"] > 0
        ), "Should return routes even in stress test"
        # Note: With improved distance calculation, we only include walking distances
        # Long-distance transit routes will have modest walking totals (~1-10km)
        assert (
            metrics.response_stats["total_distance_m"] > 500
        ), "Routes should have some walking distance (>500m)"

    finally:
        if "adapter" in locals():
            await adapter.motis_client.close()
        tracemalloc.stop()


if __name__ == "__main__":
    # Allow running benchmarks directly
    async def main():
        print("Running AB Routing Benchmarks...")
        await test_motis_ab_routing_performance_benchmark()
        await test_motis_ab_routing_minimal_benchmark()
        await test_motis_ab_routing_stress_benchmark()

    asyncio.run(main())
