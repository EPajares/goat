"""Tests for catchment area schemas and CatchmentAreaTool."""

import pytest

from goatlib.analysis.accessibility import CatchmentAreaTool
from goatlib.analysis.schemas import (
    AccessEgressMode,
    CatchmentAreaRoutingMode,
    CatchmentAreaToolParams,
    CatchmentAreaType,
    PTMode,
    PTTimeWindow,
)

# Default routing URL for tests
TEST_ROUTING_URL = "https://routing.example.com"
TEST_R5_ROUTING_URL = "https://r5.routing.example.com"


# ---------------------------------------------------------------------------
# Test: CatchmentAreaToolParams
# ---------------------------------------------------------------------------


class TestCatchmentAreaToolParams:
    """Tests for CatchmentAreaToolParams validation."""

    def test_valid_params_minimal(self) -> None:
        """Test creating params with minimal required fields."""
        params = CatchmentAreaToolParams(
            latitude=48.137,
            longitude=11.576,
            output_path="/tmp/output.parquet",
            routing_url=TEST_ROUTING_URL,
        )
        assert params.latitude == 48.137
        assert params.longitude == 11.576
        assert params.routing_mode == CatchmentAreaRoutingMode.walking

    def test_valid_params_full(self) -> None:
        """Test creating params with all fields."""
        params = CatchmentAreaToolParams(
            latitude=48.137,
            longitude=11.576,
            routing_mode=CatchmentAreaRoutingMode.bicycle,
            travel_time=20,
            steps=4,
            speed=15.0,
            catchment_area_type=CatchmentAreaType.network,
            polygon_difference=False,
            output_path="/tmp/output.geojson",
            routing_url=TEST_ROUTING_URL,
            scenario_id="test-123",
        )
        assert params.routing_mode == CatchmentAreaRoutingMode.bicycle
        assert params.travel_time == 20
        assert params.steps == 4
        assert params.speed == 15.0
        assert params.catchment_area_type == CatchmentAreaType.network

    def test_params_with_pt_settings(self) -> None:
        """Test creating params for PT routing."""
        params = CatchmentAreaToolParams(
            latitude=48.137,
            longitude=11.576,
            routing_mode=CatchmentAreaRoutingMode.pt,
            travel_time=45,
            steps=5,
            output_path="/tmp/output.parquet",
            routing_url=TEST_R5_ROUTING_URL,
            transit_modes=[PTMode.bus, PTMode.tram, PTMode.rail],
            time_window=PTTimeWindow(
                weekday="weekday",
                from_time=25200,
                to_time=32400,
            ),
        )
        assert params.routing_mode == CatchmentAreaRoutingMode.pt
        assert params.transit_modes == [PTMode.bus, PTMode.tram, PTMode.rail]
        assert params.time_window is not None

    def test_params_with_multiple_points(self) -> None:
        """Test creating params with multiple starting points."""
        params = CatchmentAreaToolParams(
            latitude=[48.137, 48.200],
            longitude=[11.576, 11.600],
            output_path="/tmp/output.parquet",
            routing_url=TEST_ROUTING_URL,
        )
        assert params.latitude == [48.137, 48.200]
        assert params.longitude == [11.576, 11.600]

    def test_pt_requires_transit_modes(self) -> None:
        """Test that PT routing requires transit_modes."""
        with pytest.raises(ValueError, match="transit_modes is required"):
            CatchmentAreaToolParams(
                latitude=48.137,
                longitude=11.576,
                routing_mode=CatchmentAreaRoutingMode.pt,
                output_path="/tmp/output.parquet",
                routing_url=TEST_R5_ROUTING_URL,
                time_window=PTTimeWindow(
                    weekday="weekday",
                    from_time=25200,
                    to_time=32400,
                ),
            )

    def test_pt_requires_time_window(self) -> None:
        """Test that PT routing requires time_window."""
        with pytest.raises(ValueError, match="time_window is required"):
            CatchmentAreaToolParams(
                latitude=48.137,
                longitude=11.576,
                routing_mode=CatchmentAreaRoutingMode.pt,
                output_path="/tmp/output.parquet",
                routing_url=TEST_R5_ROUTING_URL,
                transit_modes=[PTMode.bus],
            )

    def test_routing_url_required(self) -> None:
        """Test that routing_url is required."""
        with pytest.raises(Exception):  # ValidationError
            CatchmentAreaToolParams(
                latitude=48.137,
                longitude=11.576,
                output_path="/tmp/output.parquet",
            )

    def test_routing_url_with_authorization(self) -> None:
        """Test that routing_url and authorization can be set in params."""
        params = CatchmentAreaToolParams(
            latitude=48.137,
            longitude=11.576,
            output_path="/tmp/output.parquet",
            routing_url="https://custom-routing.example.com",
            authorization="Bearer token123",
        )
        assert params.routing_url == "https://custom-routing.example.com"
        assert params.authorization == "Bearer token123"


# ---------------------------------------------------------------------------
# Test: PTTimeWindow
# ---------------------------------------------------------------------------


class TestPTTimeWindow:
    """Tests for PTTimeWindow model."""

    def test_with_integer_times(self) -> None:
        """Test creating time window with integer seconds."""
        tw = PTTimeWindow(weekday="weekday", from_time=25200, to_time=32400)
        assert tw.from_time == 25200
        assert tw.to_time == 32400

    def test_weekday_values(self) -> None:
        """Test all weekday values."""
        for day in ["weekday", "saturday", "sunday"]:
            tw = PTTimeWindow(weekday=day, from_time=25200, to_time=32400)
            assert tw.weekday == day


# ---------------------------------------------------------------------------
# Test: Enums
# ---------------------------------------------------------------------------


class TestEnums:
    """Tests for catchment area enums."""

    def test_routing_modes(self) -> None:
        """Test all routing mode values."""
        assert CatchmentAreaRoutingMode.walking.value == "walking"
        assert CatchmentAreaRoutingMode.bicycle.value == "bicycle"
        assert CatchmentAreaRoutingMode.pedelec.value == "pedelec"
        assert CatchmentAreaRoutingMode.wheelchair.value == "wheelchair"
        assert CatchmentAreaRoutingMode.car.value == "car"
        assert CatchmentAreaRoutingMode.pt.value == "pt"

    def test_catchment_area_types(self) -> None:
        """Test all catchment area type values."""
        assert CatchmentAreaType.polygon.value == "polygon"
        assert CatchmentAreaType.network.value == "network"
        assert CatchmentAreaType.rectangular_grid.value == "rectangular_grid"

    def test_pt_modes(self) -> None:
        """Test PT mode values."""
        assert PTMode.bus.value == "bus"
        assert PTMode.tram.value == "tram"
        assert PTMode.rail.value == "rail"
        assert PTMode.subway.value == "subway"

    def test_access_egress_modes(self) -> None:
        """Test access/egress mode values."""
        assert AccessEgressMode.walk.value == "walk"
        assert AccessEgressMode.bicycle.value == "bicycle"
        assert AccessEgressMode.car.value == "car"


# ---------------------------------------------------------------------------
# Test: CatchmentAreaTool
# ---------------------------------------------------------------------------


class TestCatchmentAreaTool:
    """Tests for the CatchmentAreaTool initialization."""

    def test_tool_initialization_defaults(self) -> None:
        """Test tool can be initialized with defaults."""
        tool = CatchmentAreaTool()
        assert tool is not None

    def test_tool_initialization_with_url(self) -> None:
        """Test tool initialization with custom URL."""
        tool = CatchmentAreaTool(
            routing_url="https://routing.example.com",
            authorization="Bearer test-token",
        )
        assert tool._default_routing_url == "https://routing.example.com"
        assert tool._default_authorization == "Bearer test-token"

    def test_tool_initialization_with_r5_config(self) -> None:
        """Test tool initialization with R5 region/bundle config."""
        tool = CatchmentAreaTool(
            r5_region_id="test-region",
            r5_bundle_id="test-bundle",
        )
        assert tool._r5_region_id == "test-region"
        assert tool._r5_bundle_id == "test-bundle"

    def test_tool_initialization_with_region_mapping(self) -> None:
        """Test tool initialization with R5 region mapping parquet path."""
        tool = CatchmentAreaTool(
            r5_region_mapping_path="/path/to/region_mapping.parquet",
        )
        assert tool._r5_region_mapping_path == "/path/to/region_mapping.parquet"

    def test_get_routing_url_from_params(self) -> None:
        """Test that routing URL from params takes precedence."""
        tool = CatchmentAreaTool(routing_url="https://default.example.com")
        params = CatchmentAreaToolParams(
            latitude=48.137,
            longitude=11.576,
            output_path="/tmp/output.parquet",
            routing_url="https://override.example.com",
        )
        assert tool._get_routing_url(params) == "https://override.example.com"

    def test_get_routing_url_uses_params(self) -> None:
        """Test that params routing_url is always used (it's mandatory)."""
        tool = CatchmentAreaTool(routing_url="https://default.example.com")
        params = CatchmentAreaToolParams(
            latitude=48.137,
            longitude=11.576,
            output_path="/tmp/output.parquet",
            routing_url="https://params.example.com",
        )
        # Since routing_url is mandatory in params, it should always be used
        assert tool._get_routing_url(params) == "https://params.example.com"
