"""Tests for analytics service."""

from unittest.mock import MagicMock, patch

from processes.services.analytics_service import (
    AnalyticsService,
    analytics_service,
)


class TestAnalyticsServiceSingleton:
    """Tests for analytics service singleton."""

    def test_singleton_exists(self):
        """Test global analytics_service instance exists."""
        assert analytics_service is not None
        assert isinstance(analytics_service, AnalyticsService)


class TestAnalyticsServiceTableName:
    """Tests for _get_table_name method."""

    def test_get_table_name_format(self):
        """Test table name is properly formatted."""
        service = AnalyticsService()

        with patch(
            "processes.services.analytics_service.normalize_layer_id"
        ) as mock_normalize:
            with patch(
                "processes.services.analytics_service.get_schema_for_layer"
            ) as mock_schema:
                with patch(
                    "processes.services.analytics_service._layer_id_to_table_name"
                ) as mock_table:
                    mock_normalize.return_value = "abc12345678901234567890123456789ab"
                    mock_schema.return_value = "user_xyz123"
                    mock_table.return_value = "t_abc12345678901234567890123456789ab"

                    result = service._get_table_name(
                        "abc12345-6789-0123-4567-890123456789"
                    )

                    assert (
                        result
                        == "lake.user_xyz123.t_abc12345678901234567890123456789ab"
                    )


class TestAnalyticsServiceBuildWhereClause:
    """Tests for _build_where_clause method."""

    def test_build_where_clause_none(self):
        """Test with no filter returns TRUE."""
        service = AnalyticsService()

        where, params = service._build_where_clause(None)

        assert where == "TRUE"
        assert params == []

    def test_build_where_clause_empty(self):
        """Test with empty filter returns TRUE."""
        service = AnalyticsService()

        where, params = service._build_where_clause("")

        assert where == "TRUE"
        assert params == []

    def test_build_where_clause_with_filter(self):
        """Test with valid CQL2 filter."""
        service = AnalyticsService()

        with patch("processes.services.analytics_service.build_filters") as mock_build:
            mock_build.return_value = ("name = ?", ["test"])

            where, params = service._build_where_clause("name = 'test'")

            assert where == "name = ?"
            assert params == ["test"]

    def test_build_where_clause_invalid_filter(self):
        """Test with invalid filter returns TRUE."""
        service = AnalyticsService()

        with patch("processes.services.analytics_service.build_filters") as mock_build:
            mock_build.side_effect = Exception("Parse error")

            where, params = service._build_where_clause("invalid filter <<<")

            assert where == "TRUE"
            assert params == []


class TestAnalyticsServiceFeatureCount:
    """Tests for feature_count method."""

    def test_feature_count_success(self):
        """Test successful feature count."""
        service = AnalyticsService()

        with patch.object(service, "_get_table_name") as mock_table:
            with patch.object(service, "_build_where_clause") as mock_where:
                with patch(
                    "processes.services.analytics_service.ducklake_manager"
                ) as mock_dm:
                    with patch(
                        "processes.services.analytics_service.calculate_feature_count"
                    ) as mock_calc:
                        mock_table.return_value = "lake.schema.table"
                        mock_where.return_value = ("TRUE", [])

                        mock_conn = MagicMock()
                        mock_dm.connection.return_value.__enter__ = MagicMock(
                            return_value=mock_conn
                        )
                        mock_dm.connection.return_value.__exit__ = MagicMock(
                            return_value=None
                        )

                        mock_result = MagicMock()
                        mock_result.model_dump.return_value = {"count": 42}
                        mock_calc.return_value = mock_result

                        result = service.feature_count("layer-123")

                        assert result["count"] == 42
                        mock_calc.assert_called_once()

    def test_feature_count_with_filter(self):
        """Test feature count with filter."""
        service = AnalyticsService()

        with patch.object(service, "_get_table_name") as mock_table:
            with patch.object(service, "_build_where_clause") as mock_where:
                with patch(
                    "processes.services.analytics_service.ducklake_manager"
                ) as mock_dm:
                    with patch(
                        "processes.services.analytics_service.calculate_feature_count"
                    ) as mock_calc:
                        mock_table.return_value = "lake.schema.table"
                        mock_where.return_value = ("category = ?", ["A"])

                        mock_conn = MagicMock()
                        mock_dm.connection.return_value.__enter__ = MagicMock(
                            return_value=mock_conn
                        )
                        mock_dm.connection.return_value.__exit__ = MagicMock(
                            return_value=None
                        )

                        mock_result = MagicMock()
                        mock_result.model_dump.return_value = {"count": 10}
                        mock_calc.return_value = mock_result

                        result = service.feature_count(
                            "layer-123", filter_expr="category='A'"
                        )

                        assert result["count"] == 10


class TestAnalyticsServiceUniqueValues:
    """Tests for unique_values method."""

    def test_unique_values_success(self):
        """Test successful unique values calculation."""
        service = AnalyticsService()

        with patch.object(service, "_get_table_name") as mock_table:
            with patch.object(service, "_build_where_clause") as mock_where:
                with patch(
                    "processes.services.analytics_service.ducklake_manager"
                ) as mock_dm:
                    with patch(
                        "processes.services.analytics_service.calculate_unique_values"
                    ) as mock_calc:
                        mock_table.return_value = "lake.schema.table"
                        mock_where.return_value = ("TRUE", [])

                        mock_conn = MagicMock()
                        mock_dm.connection.return_value.__enter__ = MagicMock(
                            return_value=mock_conn
                        )
                        mock_dm.connection.return_value.__exit__ = MagicMock(
                            return_value=None
                        )

                        mock_result = MagicMock()
                        mock_result.model_dump.return_value = {
                            "values": [
                                {"value": "A", "count": 10},
                                {"value": "B", "count": 5},
                            ]
                        }
                        mock_calc.return_value = mock_result

                        result = service.unique_values("layer-123", "category")

                        assert len(result["values"]) == 2
                        assert result["values"][0]["value"] == "A"


class TestAnalyticsServiceClassBreaks:
    """Tests for class_breaks method."""

    def test_class_breaks_success(self):
        """Test successful class breaks calculation."""
        service = AnalyticsService()

        with patch.object(service, "_get_table_name") as mock_table:
            with patch.object(service, "_build_where_clause") as mock_where:
                with patch(
                    "processes.services.analytics_service.ducklake_manager"
                ) as mock_dm:
                    with patch(
                        "processes.services.analytics_service.calculate_class_breaks"
                    ) as mock_calc:
                        mock_table.return_value = "lake.schema.table"
                        mock_where.return_value = ("TRUE", [])

                        mock_conn = MagicMock()
                        mock_dm.connection.return_value.__enter__ = MagicMock(
                            return_value=mock_conn
                        )
                        mock_dm.connection.return_value.__exit__ = MagicMock(
                            return_value=None
                        )

                        mock_result = MagicMock()
                        mock_result.model_dump.return_value = {
                            "breaks": [0, 25, 50, 75, 100],
                            "method": "quantile",
                        }
                        mock_calc.return_value = mock_result

                        # Use 'breaks' param (not 'num_classes')
                        result = service.class_breaks(
                            "layer-123", "population", breaks=5
                        )

                        assert len(result["breaks"]) == 5
                        assert result["method"] == "quantile"


class TestAnalyticsServiceAreaStatistics:
    """Tests for area_statistics method."""

    def test_area_statistics_success(self):
        """Test successful area statistics calculation."""
        service = AnalyticsService()

        with patch.object(service, "_get_table_name") as mock_table:
            with patch.object(service, "_build_where_clause") as mock_where:
                with patch(
                    "processes.services.analytics_service.ducklake_manager"
                ) as mock_dm:
                    with patch(
                        "processes.services.analytics_service.calculate_area_statistics"
                    ) as mock_calc:
                        mock_table.return_value = "lake.schema.table"
                        mock_where.return_value = ("TRUE", [])

                        mock_conn = MagicMock()
                        mock_dm.connection.return_value.__enter__ = MagicMock(
                            return_value=mock_conn
                        )
                        mock_dm.connection.return_value.__exit__ = MagicMock(
                            return_value=None
                        )

                        mock_result = MagicMock()
                        mock_result.model_dump.return_value = {
                            "total_area": 1000.5,
                            "unit": "square_meters",
                        }
                        mock_calc.return_value = mock_result

                        result = service.area_statistics("layer-123", operation="sum")

                        assert result["total_area"] == 1000.5
                        assert result["unit"] == "square_meters"
