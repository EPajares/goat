"""Tests for catchment area schemas."""

from pathlib import Path

import pytest

from goatlib.analysis.schemas import (
    ActiveMobilityMode,
    CatchmentAreaActiveMobilityRequest,
    CatchmentAreaCarRequest,
    CatchmentAreaPTRequest,
    CatchmentAreaResponse,
    CatchmentAreaType,
    Coordinates,
    OutputFormat,
    PTSettings,
    PTTimeWindow,
    StartingPoints,
    TravelDistanceCost,
    TravelTimeCost,
    TravelTimeCostPT,
)
from goatlib.routing.interfaces.mocks import MockCatchmentAreaService


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def munich_coordinates() -> Coordinates:
    """Munich city center coordinates."""
    return Coordinates(lat=48.137154, lon=11.576124)


@pytest.fixture
def starting_points(munich_coordinates: Coordinates) -> StartingPoints:
    """Starting points fixture with Munich coordinates."""
    return StartingPoints(coordinates=[munich_coordinates])


@pytest.fixture
def travel_time_cost() -> TravelTimeCost:
    """Standard travel time cost for 15 minutes."""
    return TravelTimeCost(max_traveltime=15, traveltime_step=5)


@pytest.fixture
def travel_distance_cost() -> TravelDistanceCost:
    """Standard travel distance cost for 1km."""
    return TravelDistanceCost(max_distance=1000, distance_step=200)


@pytest.fixture
def pt_time_window() -> PTTimeWindow:
    """Morning rush hour time window."""
    return PTTimeWindow(weekday="weekday", from_time=25200, to_time=32400)


@pytest.fixture
def pt_settings(pt_time_window: PTTimeWindow) -> PTSettings:
    """Standard PT settings."""
    return PTSettings(time_window=pt_time_window)


@pytest.fixture
def mock_service() -> MockCatchmentAreaService:
    """Mock catchment area service."""
    return MockCatchmentAreaService()


# ---------------------------------------------------------------------------
# Test: Coordinates and StartingPoints
# ---------------------------------------------------------------------------


class TestCoordinates:
    """Tests for Coordinates model."""

    def test_valid_coordinates(self) -> None:
        """Test creating valid coordinates."""
        coord = Coordinates(lat=48.137, lon=11.576)
        assert coord.lat == 48.137
        assert coord.lon == 11.576

    def test_invalid_latitude_too_high(self) -> None:
        """Test that latitude > 90 raises error."""
        with pytest.raises(ValueError):
            Coordinates(lat=91.0, lon=11.576)

    def test_invalid_latitude_too_low(self) -> None:
        """Test that latitude < -90 raises error."""
        with pytest.raises(ValueError):
            Coordinates(lat=-91.0, lon=11.576)

    def test_invalid_longitude_too_high(self) -> None:
        """Test that longitude > 180 raises error."""
        with pytest.raises(ValueError):
            Coordinates(lat=48.137, lon=181.0)

    def test_invalid_longitude_too_low(self) -> None:
        """Test that longitude < -180 raises error."""
        with pytest.raises(ValueError):
            Coordinates(lat=48.137, lon=-181.0)


class TestStartingPoints:
    """Tests for StartingPoints model."""

    def test_with_coordinates_list(self, munich_coordinates: Coordinates) -> None:
        """Test creating starting points with coordinates list."""
        sp = StartingPoints(coordinates=[munich_coordinates])
        assert len(sp.coordinates) == 1
        assert sp.coordinates[0].lat == munich_coordinates.lat

    def test_with_legacy_lat_lon(self) -> None:
        """Test creating starting points with legacy lat/lon lists."""
        sp = StartingPoints(latitude=[48.137], longitude=[11.576])
        assert sp.latitude == [48.137]
        assert sp.longitude == [11.576]

    def test_to_coordinates_from_legacy(self) -> None:
        """Test converting legacy format to coordinates."""
        sp = StartingPoints(latitude=[48.137, 48.200], longitude=[11.576, 11.600])
        coords = sp.to_coordinates()
        assert len(coords) == 2
        assert coords[0].lat == 48.137
        assert coords[1].lon == 11.600

    def test_empty_raises_error(self) -> None:
        """Test that empty starting points raises error."""
        with pytest.raises(ValueError):
            StartingPoints(coordinates=[])

    def test_mismatched_lat_lon_raises_error(self) -> None:
        """Test that mismatched lat/lon lists raises error."""
        with pytest.raises(ValueError):
            StartingPoints(latitude=[48.137, 48.200], longitude=[11.576])


# ---------------------------------------------------------------------------
# Test: Travel Cost
# ---------------------------------------------------------------------------


class TestTravelCost:
    """Tests for travel cost models."""

    def test_travel_time_cost_valid(self) -> None:
        """Test valid travel time cost."""
        cost = TravelTimeCost(max_traveltime=30, traveltime_step=10)
        assert cost.max_traveltime == 30
        assert cost.traveltime_step == 10

    def test_travel_distance_cost_valid(self) -> None:
        """Test valid travel distance cost."""
        cost = TravelDistanceCost(max_distance=5000, distance_step=500)
        assert cost.max_distance == 5000
        assert cost.distance_step == 500

    def test_travel_time_cost_pt_with_steps(self) -> None:
        """Test PT travel cost with custom steps."""
        cost = TravelTimeCostPT(max_traveltime=60, steps=[15, 30, 45, 60])
        assert cost.max_traveltime == 60
        assert cost.steps == [15, 30, 45, 60]


# ---------------------------------------------------------------------------
# Test: Active Mobility Request
# ---------------------------------------------------------------------------


class TestActiveMobilityRequest:
    """Tests for active mobility catchment area requests."""

    def test_create_from_fixtures(
        self, starting_points: StartingPoints, travel_time_cost: TravelTimeCost
    ) -> None:
        """Test creating request from fixtures."""
        request = CatchmentAreaActiveMobilityRequest(
            starting_points=starting_points,
            routing_mode=ActiveMobilityMode.walk,
            travel_cost=travel_time_cost,
        )
        assert request.mode == "active_mobility"
        assert request.routing_mode == ActiveMobilityMode.walk

    def test_create_from_json_data(self, starting_points: StartingPoints) -> None:
        """Test creating request from dict data (simulating JSON deserialization)."""
        request_data = {
            "starting_points": {"coordinates": [{"lat": 48.137154, "lon": 11.576124}]},
            "routing_mode": "walk",
            "travel_cost": {"max_traveltime": 15, "traveltime_step": 5},
        }
        request = CatchmentAreaActiveMobilityRequest(**request_data)
        assert request.routing_mode == ActiveMobilityMode.walk
        assert request.travel_cost.max_traveltime == 15

    def test_all_active_mobility_modes(
        self, starting_points: StartingPoints, travel_time_cost: TravelTimeCost
    ) -> None:
        """Test all active mobility modes."""
        for mode in ActiveMobilityMode:
            request = CatchmentAreaActiveMobilityRequest(
                starting_points=starting_points,
                routing_mode=mode,
                travel_cost=travel_time_cost,
            )
            assert request.routing_mode == mode

    def test_with_distance_cost(
        self, starting_points: StartingPoints, travel_distance_cost: TravelDistanceCost
    ) -> None:
        """Test request with distance-based cost."""
        request = CatchmentAreaActiveMobilityRequest(
            starting_points=starting_points,
            routing_mode=ActiveMobilityMode.bicycle,
            travel_cost=travel_distance_cost,
        )
        assert request.travel_cost.max_distance == 1000


# ---------------------------------------------------------------------------
# Test: PT Request
# ---------------------------------------------------------------------------


class TestPTRequest:
    """Tests for public transport catchment area requests."""

    def test_create_from_fixtures(
        self, starting_points: StartingPoints, pt_settings: PTSettings
    ) -> None:
        """Test creating PT request from fixtures."""
        request = CatchmentAreaPTRequest(
            starting_points=starting_points,
            travel_cost=TravelTimeCostPT(max_traveltime=45),
            settings=pt_settings,
        )
        assert request.mode == "pt"
        assert request.routing_provider.value == "r5"

    def test_create_with_all_params(
        self, starting_points: StartingPoints, pt_settings: PTSettings
    ) -> None:
        """Test creating PT request with all parameters."""
        request = CatchmentAreaPTRequest(
            starting_points=starting_points,
            travel_cost=TravelTimeCostPT(max_traveltime=60, traveltime_step=15),
            settings=pt_settings,
        )
        assert request.settings.access_mode.value == "walk"
        assert request.travel_cost.max_traveltime == 60


# ---------------------------------------------------------------------------
# Test: Response
# ---------------------------------------------------------------------------


class TestCatchmentAreaResponse:
    """Tests for catchment area response."""

    def test_create_from_dict_data(self) -> None:
        """Test creating response from dict data (simulating JSON deserialization)."""
        response_data = {
            "starting_point": {"lat": 48.137154, "lon": 11.576124},
            "catchment_area_type": "polygon",
            "polygons": [
                {
                    "travel_cost": 5,
                    "geometry": {
                        "type": "Polygon",
                        "coordinates": [
                            [
                                [11.57, 48.135],
                                [11.58, 48.135],
                                [11.58, 48.14],
                                [11.57, 48.14],
                                [11.57, 48.135],
                            ]
                        ],
                    },
                },
                {
                    "travel_cost": 10,
                    "geometry": {
                        "type": "Polygon",
                        "coordinates": [
                            [
                                [11.565, 48.13],
                                [11.585, 48.13],
                                [11.585, 48.145],
                                [11.565, 48.145],
                                [11.565, 48.13],
                            ]
                        ],
                    },
                },
                {
                    "travel_cost": 15,
                    "geometry": {
                        "type": "Polygon",
                        "coordinates": [
                            [
                                [11.56, 48.125],
                                [11.59, 48.125],
                                [11.59, 48.15],
                                [11.56, 48.15],
                                [11.56, 48.125],
                            ]
                        ],
                    },
                },
            ],
            "metadata": {"provider": "test"},
        }
        response = CatchmentAreaResponse(**response_data)
        assert response.starting_point.lat == 48.137154
        assert response.catchment_area_type == CatchmentAreaType.polygon
        assert len(response.polygons) == 3
        assert response.polygons[0].travel_cost == 5


# ---------------------------------------------------------------------------
# Test: Mock Service
# ---------------------------------------------------------------------------


class TestMockCatchmentAreaService:
    """Tests for mock catchment area service."""

    @pytest.mark.asyncio
    async def test_active_mobility_returns_response(
        self,
        mock_service: MockCatchmentAreaService,
        starting_points: StartingPoints,
        travel_time_cost: TravelTimeCost,
    ) -> None:
        """Test mock service returns valid response for active mobility."""
        request = CatchmentAreaActiveMobilityRequest(
            starting_points=starting_points,
            routing_mode=ActiveMobilityMode.walk,
            travel_cost=travel_time_cost,
        )
        response = await mock_service.compute_active_mobility_catchment(request)

        assert response.starting_point.lat == 48.137154
        assert response.catchment_area_type == CatchmentAreaType.polygon
        assert response.metadata.get("provider") == "mock"

    @pytest.mark.asyncio
    async def test_call_history_tracking(
        self,
        mock_service: MockCatchmentAreaService,
        starting_points: StartingPoints,
        travel_time_cost: TravelTimeCost,
    ) -> None:
        """Test that mock service tracks call history."""
        request = CatchmentAreaActiveMobilityRequest(
            starting_points=starting_points,
            routing_mode=ActiveMobilityMode.bicycle,
            travel_cost=travel_time_cost,
        )

        assert len(mock_service.call_history) == 0
        await mock_service.compute_active_mobility_catchment(request)
        assert len(mock_service.call_history) == 1
        assert (
            mock_service.call_history[0]["method"]
            == "compute_active_mobility_catchment"
        )

    @pytest.mark.asyncio
    async def test_reset_clears_history(
        self,
        mock_service: MockCatchmentAreaService,
        starting_points: StartingPoints,
        travel_time_cost: TravelTimeCost,
    ) -> None:
        """Test that reset clears call history."""
        request = CatchmentAreaActiveMobilityRequest(
            starting_points=starting_points,
            routing_mode=ActiveMobilityMode.walk,
            travel_cost=travel_time_cost,
        )

        await mock_service.compute_active_mobility_catchment(request)
        assert len(mock_service.call_history) == 1

        mock_service.reset()
        assert len(mock_service.call_history) == 0
