"""Tests for OGC API Processes endpoints."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from geoapi.services.layer_service import LayerMetadata


@pytest.fixture
def sample_layer_metadata_with_numeric():
    """Sample layer metadata with numeric columns for testing."""
    return LayerMetadata(
        layer_id="abc123def4567890123456789012345b",
        name="Test Layer",
        geometry_type="Polygon",
        bounds=[-180, -90, 180, 90],
        columns=[
            {"name": "id", "type": "uuid", "json_type": "string"},
            {"name": "name", "type": "varchar", "json_type": "string"},
            {"name": "category", "type": "varchar", "json_type": "string"},
            {"name": "value", "type": "double", "json_type": "number"},
            {"name": "count", "type": "integer", "json_type": "integer"},
            {"name": "geometry", "type": "geometry", "json_type": "geometry"},
        ],
        user_id="d78bf1ae72f541048f0cf48c80f3f63b",
        geometry_column="geometry",
    )


class TestProcessList:
    """Tests for process list endpoint."""

    def test_get_processes(self, test_client):
        """Test listing all available processes."""
        response = test_client.get("/processes")
        assert response.status_code == 200
        data = response.json()

        assert "processes" in data
        assert "links" in data
        assert len(data["processes"]) == 4

        # Check process IDs
        process_ids = [p["id"] for p in data["processes"]]
        assert "feature-count" in process_ids
        assert "area-statistics" in process_ids
        assert "unique-values" in process_ids
        assert "class-breaks" in process_ids

    def test_process_list_structure(self, test_client):
        """Test that process list has correct structure."""
        response = test_client.get("/processes")
        data = response.json()

        for process in data["processes"]:
            assert "id" in process
            assert "title" in process
            assert "description" in process
            assert "version" in process
            assert "jobControlOptions" in process
            assert "outputTransmission" in process
            assert "links" in process

            # Check job control options
            assert "sync-execute" in process["jobControlOptions"]

    def test_process_list_links(self, test_client):
        """Test that process list has proper self link."""
        response = test_client.get("/processes")
        data = response.json()

        rels = [link["rel"] for link in data["links"]]
        assert "self" in rels


class TestProcessDescription:
    """Tests for process description endpoint."""

    def test_get_feature_count_process(self, test_client):
        """Test getting feature-count process description."""
        response = test_client.get("/processes/feature-count")
        assert response.status_code == 200
        data = response.json()

        assert data["id"] == "feature-count"
        assert data["title"] == "Feature Count"
        assert "inputs" in data
        assert "outputs" in data

        # Check inputs
        assert "collection" in data["inputs"]
        assert "filter" in data["inputs"]
        assert data["inputs"]["collection"]["minOccurs"] == 1
        assert data["inputs"]["filter"]["minOccurs"] == 0

        # Check outputs
        assert "count" in data["outputs"]

    def test_get_area_statistics_process(self, test_client):
        """Test getting area-statistics process description."""
        response = test_client.get("/processes/area-statistics")
        assert response.status_code == 200
        data = response.json()

        assert data["id"] == "area-statistics"
        assert "inputs" in data
        assert "collection" in data["inputs"]
        assert "operation" in data["inputs"]

    def test_get_unique_values_process(self, test_client):
        """Test getting unique-values process description."""
        response = test_client.get("/processes/unique-values")
        assert response.status_code == 200
        data = response.json()

        assert data["id"] == "unique-values"
        assert "attribute" in data["inputs"]
        assert "order" in data["inputs"]
        assert "limit" in data["inputs"]

    def test_get_class_breaks_process(self, test_client):
        """Test getting class-breaks process description."""
        response = test_client.get("/processes/class-breaks")
        assert response.status_code == 200
        data = response.json()

        assert data["id"] == "class-breaks"
        assert "attribute" in data["inputs"]
        assert "method" in data["inputs"]
        assert "breaks" in data["inputs"]

    def test_get_nonexistent_process(self, test_client):
        """Test getting a non-existent process returns 404."""
        response = test_client.get("/processes/nonexistent")
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data

    def test_process_has_execute_link(self, test_client):
        """Test that process description includes execute link."""
        response = test_client.get("/processes/feature-count")
        data = response.json()

        rels = [link["rel"] for link in data["links"]]
        assert "http://www.opengis.net/def/rel/ogc/1.0/execute" in rels


class TestFeatureCountExecution:
    """Tests for feature-count process execution."""

    @patch("geoapi.services.process_service.layer_service")
    @patch("geoapi.services.process_service.ducklake_manager")
    def test_execute_feature_count(
        self,
        mock_ducklake,
        mock_layer_service,
        test_client,
        sample_layer_metadata_with_numeric,
    ):
        """Test executing feature-count process."""
        # Mock layer service
        mock_layer_service.get_metadata_by_id = AsyncMock(
            return_value=sample_layer_metadata_with_numeric
        )

        # Mock DuckDB connection
        mock_conn = MagicMock()
        mock_conn.execute.return_value.fetchone.return_value = (42,)
        mock_ducklake.connection.return_value.__enter__ = MagicMock(
            return_value=mock_conn
        )
        mock_ducklake.connection.return_value.__exit__ = MagicMock(return_value=None)

        response = test_client.post(
            "/processes/feature-count/execution",
            json={"inputs": {"collection": "abc123de-f456-7890-1234-567890123456"}},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 42

    @patch("geoapi.services.process_service.layer_service")
    @patch("geoapi.services.process_service.ducklake_manager")
    def test_execute_feature_count_with_filter(
        self,
        mock_ducklake,
        mock_layer_service,
        test_client,
        sample_layer_metadata_with_numeric,
    ):
        """Test executing feature-count with CQL2 filter."""
        mock_layer_service.get_metadata_by_id = AsyncMock(
            return_value=sample_layer_metadata_with_numeric
        )

        mock_conn = MagicMock()
        mock_conn.execute.return_value.fetchone.return_value = (10,)
        mock_ducklake.connection.return_value.__enter__ = MagicMock(
            return_value=mock_conn
        )
        mock_ducklake.connection.return_value.__exit__ = MagicMock(return_value=None)

        cql_filter = '{"op": "=", "args": [{"property": "name"}, "Berlin"]}'
        response = test_client.post(
            "/processes/feature-count/execution",
            json={
                "inputs": {
                    "collection": "abc123de-f456-7890-1234-567890123456",
                    "filter": cql_filter,
                }
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 10

    def test_execute_feature_count_missing_collection(self, test_client):
        """Test feature-count fails without collection parameter."""
        response = test_client.post(
            "/processes/feature-count/execution",
            json={"inputs": {}},
        )
        assert response.status_code == 400

    @patch("geoapi.services.process_service.layer_service")
    def test_execute_feature_count_collection_not_found(
        self, mock_layer_service, test_client
    ):
        """Test feature-count with non-existent collection."""
        mock_layer_service.get_metadata_by_id = AsyncMock(return_value=None)

        response = test_client.post(
            "/processes/feature-count/execution",
            json={"inputs": {"collection": "abc123de-f456-7890-1234-567890123456"}},
        )
        assert response.status_code == 400


class TestAreaStatisticsExecution:
    """Tests for area-statistics process execution."""

    @patch("geoapi.services.process_service.layer_service")
    @patch("geoapi.services.process_service.ducklake_manager")
    def test_execute_area_statistics_sum(
        self,
        mock_ducklake,
        mock_layer_service,
        test_client,
        sample_layer_metadata_with_numeric,
    ):
        """Test executing area-statistics with sum operation."""
        mock_layer_service.get_metadata_by_id = AsyncMock(
            return_value=sample_layer_metadata_with_numeric
        )

        mock_conn = MagicMock()
        # Return (total_area, feature_count, result)
        mock_conn.execute.return_value.fetchone.return_value = (1000.0, 5, 1000.0)
        mock_ducklake.connection.return_value.__enter__ = MagicMock(
            return_value=mock_conn
        )
        mock_ducklake.connection.return_value.__exit__ = MagicMock(return_value=None)

        response = test_client.post(
            "/processes/area-statistics/execution",
            json={
                "inputs": {
                    "collection": "abc123de-f456-7890-1234-567890123456",
                    "operation": "sum",
                }
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert "total_area" in data
        assert "feature_count" in data
        assert "result" in data
        assert "unit" in data

    @patch("geoapi.services.process_service.layer_service")
    @patch("geoapi.services.process_service.ducklake_manager")
    def test_execute_area_statistics_mean(
        self,
        mock_ducklake,
        mock_layer_service,
        test_client,
        sample_layer_metadata_with_numeric,
    ):
        """Test executing area-statistics with mean operation."""
        mock_layer_service.get_metadata_by_id = AsyncMock(
            return_value=sample_layer_metadata_with_numeric
        )

        mock_conn = MagicMock()
        mock_conn.execute.return_value.fetchone.return_value = (1000.0, 5, 200.0)
        mock_ducklake.connection.return_value.__enter__ = MagicMock(
            return_value=mock_conn
        )
        mock_ducklake.connection.return_value.__exit__ = MagicMock(return_value=None)

        response = test_client.post(
            "/processes/area-statistics/execution",
            json={
                "inputs": {
                    "collection": "abc123de-f456-7890-1234-567890123456",
                    "operation": "mean",
                }
            },
        )

        assert response.status_code == 200

    def test_execute_area_statistics_invalid_operation(self, test_client):
        """Test area-statistics with invalid operation."""
        response = test_client.post(
            "/processes/area-statistics/execution",
            json={
                "inputs": {
                    "collection": "abc123de-f456-7890-1234-567890123456",
                    "operation": "invalid",
                }
            },
        )
        assert response.status_code == 400


class TestUniqueValuesExecution:
    """Tests for unique-values process execution."""

    @patch("geoapi.services.process_service.layer_service")
    @patch("geoapi.services.process_service.ducklake_manager")
    def test_execute_unique_values(
        self,
        mock_ducklake,
        mock_layer_service,
        test_client,
        sample_layer_metadata_with_numeric,
    ):
        """Test executing unique-values process."""
        mock_layer_service.get_metadata_by_id = AsyncMock(
            return_value=sample_layer_metadata_with_numeric
        )

        mock_conn = MagicMock()
        # Return unique values with counts
        mock_conn.execute.return_value.fetchall.return_value = [
            ("category_a", 10),
            ("category_b", 5),
            ("category_c", 3),
        ]
        mock_ducklake.connection.return_value.__enter__ = MagicMock(
            return_value=mock_conn
        )
        mock_ducklake.connection.return_value.__exit__ = MagicMock(return_value=None)

        response = test_client.post(
            "/processes/unique-values/execution",
            json={
                "inputs": {
                    "collection": "abc123de-f456-7890-1234-567890123456",
                    "attribute": "category",
                }
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert "values" in data
        assert "total" in data
        assert len(data["values"]) == 3

    @patch("geoapi.services.process_service.layer_service")
    def test_execute_unique_values_invalid_attribute(
        self, mock_layer_service, test_client, sample_layer_metadata_with_numeric
    ):
        """Test unique-values with non-existent attribute."""
        mock_layer_service.get_metadata_by_id = AsyncMock(
            return_value=sample_layer_metadata_with_numeric
        )

        response = test_client.post(
            "/processes/unique-values/execution",
            json={
                "inputs": {
                    "collection": "abc123de-f456-7890-1234-567890123456",
                    "attribute": "nonexistent",
                }
            },
        )
        assert response.status_code == 400

    @patch("geoapi.services.process_service.layer_service")
    @patch("geoapi.services.process_service.ducklake_manager")
    def test_execute_unique_values_with_limit(
        self,
        mock_ducklake,
        mock_layer_service,
        test_client,
        sample_layer_metadata_with_numeric,
    ):
        """Test unique-values with limit parameter."""
        mock_layer_service.get_metadata_by_id = AsyncMock(
            return_value=sample_layer_metadata_with_numeric
        )

        mock_conn = MagicMock()
        mock_conn.execute.return_value.fetchall.return_value = [
            ("category_a", 10),
        ]
        mock_ducklake.connection.return_value.__enter__ = MagicMock(
            return_value=mock_conn
        )
        mock_ducklake.connection.return_value.__exit__ = MagicMock(return_value=None)

        response = test_client.post(
            "/processes/unique-values/execution",
            json={
                "inputs": {
                    "collection": "abc123de-f456-7890-1234-567890123456",
                    "attribute": "category",
                    "limit": 1,
                }
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["values"]) == 1


class TestClassBreaksExecution:
    """Tests for class-breaks process execution."""

    @patch("geoapi.services.process_service.layer_service")
    @patch("geoapi.services.process_service.ducklake_manager")
    def test_execute_class_breaks_quantile(
        self,
        mock_ducklake,
        mock_layer_service,
        test_client,
        sample_layer_metadata_with_numeric,
    ):
        """Test executing class-breaks with quantile method."""
        mock_layer_service.get_metadata_by_id = AsyncMock(
            return_value=sample_layer_metadata_with_numeric
        )

        mock_conn = MagicMock()
        # Stats query returns (min, max, mean, stddev)
        mock_conn.execute.return_value.fetchone.return_value = (0.0, 100.0, 50.0, 25.0)
        # Quantile breaks query
        mock_conn.execute.return_value.fetchall.return_value = [
            (20.0,),
            (40.0,),
            (60.0,),
            (80.0,),
        ]
        mock_ducklake.connection.return_value.__enter__ = MagicMock(
            return_value=mock_conn
        )
        mock_ducklake.connection.return_value.__exit__ = MagicMock(return_value=None)

        response = test_client.post(
            "/processes/class-breaks/execution",
            json={
                "inputs": {
                    "collection": "abc123de-f456-7890-1234-567890123456",
                    "attribute": "value",
                    "method": "quantile",
                    "breaks": 5,
                }
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert "breaks" in data
        assert "min" in data
        assert "max" in data
        assert "method" in data
        assert data["method"] == "quantile"
        assert data["attribute"] == "value"

    @patch("geoapi.services.process_service.layer_service")
    @patch("geoapi.services.process_service.ducklake_manager")
    def test_execute_class_breaks_equal_interval(
        self,
        mock_ducklake,
        mock_layer_service,
        test_client,
        sample_layer_metadata_with_numeric,
    ):
        """Test executing class-breaks with equal_interval method."""
        mock_layer_service.get_metadata_by_id = AsyncMock(
            return_value=sample_layer_metadata_with_numeric
        )

        mock_conn = MagicMock()
        mock_conn.execute.return_value.fetchone.return_value = (0.0, 100.0, 50.0, 25.0)
        mock_ducklake.connection.return_value.__enter__ = MagicMock(
            return_value=mock_conn
        )
        mock_ducklake.connection.return_value.__exit__ = MagicMock(return_value=None)

        response = test_client.post(
            "/processes/class-breaks/execution",
            json={
                "inputs": {
                    "collection": "abc123de-f456-7890-1234-567890123456",
                    "attribute": "value",
                    "method": "equal_interval",
                    "breaks": 5,
                }
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["method"] == "equal_interval"

    @patch("geoapi.services.process_service.layer_service")
    @patch("geoapi.services.process_service.ducklake_manager")
    def test_execute_class_breaks_invalid_attribute(
        self,
        mock_ducklake,
        mock_layer_service,
        test_client,
        sample_layer_metadata_with_numeric,
    ):
        """Test class-breaks with non-numeric attribute."""
        mock_layer_service.get_metadata_by_id = AsyncMock(
            return_value=sample_layer_metadata_with_numeric
        )

        # Mock DuckDB connection (needed even though validation fails early)
        mock_conn = MagicMock()
        mock_ducklake.connection.return_value.__enter__ = MagicMock(
            return_value=mock_conn
        )
        mock_ducklake.connection.return_value.__exit__ = MagicMock(return_value=None)

        response = test_client.post(
            "/processes/class-breaks/execution",
            json={
                "inputs": {
                    "collection": "abc123de-f456-7890-1234-567890123456",
                    "attribute": "name",  # string column
                    "method": "quantile",
                    "breaks": 5,
                }
            },
        )
        assert response.status_code == 400

    def test_execute_class_breaks_invalid_method(self, test_client):
        """Test class-breaks with invalid method."""
        response = test_client.post(
            "/processes/class-breaks/execution",
            json={
                "inputs": {
                    "collection": "abc123de-f456-7890-1234-567890123456",
                    "attribute": "value",
                    "method": "invalid_method",
                    "breaks": 5,
                }
            },
        )
        assert response.status_code == 400


class TestProcessExecutionErrors:
    """Tests for process execution error handling."""

    def test_execute_nonexistent_process(self, test_client):
        """Test executing a non-existent process returns 404."""
        response = test_client.post(
            "/processes/nonexistent/execution",
            json={"inputs": {}},
        )
        assert response.status_code == 404

    def test_execute_invalid_collection_format(self, test_client):
        """Test executing with invalid collection UUID format."""
        response = test_client.post(
            "/processes/feature-count/execution",
            json={"inputs": {"collection": "not-a-uuid"}},
        )
        assert response.status_code == 400


class TestConformanceIncludesProcesses:
    """Tests that conformance includes OGC API Processes classes."""

    def test_conformance_includes_processes(self, test_client):
        """Test that conformance includes OGC API Processes conformance classes."""
        response = test_client.get("/conformance")
        assert response.status_code == 200
        data = response.json()

        conformance_classes = data["conformsTo"]
        assert any("ogcapi-processes" in c for c in conformance_classes)
        assert (
            "http://www.opengis.net/spec/ogcapi-processes-1/1.0/conf/core"
            in conformance_classes
        )
        assert (
            "http://www.opengis.net/spec/ogcapi-processes-1/1.0/conf/json"
            in conformance_classes
        )


class TestLandingPageIncludesProcesses:
    """Tests that landing page includes processes link."""

    def test_landing_page_has_processes_link(self, test_client):
        """Test that landing page includes link to processes."""
        response = test_client.get("/")
        assert response.status_code == 200
        data = response.json()

        # Check for processes link
        process_links = [
            link
            for link in data["links"]
            if link.get("rel") == "http://www.opengis.net/def/rel/ogc/1.0/processes"
        ]
        assert len(process_links) == 1
        assert "/processes" in process_links[0]["href"]
