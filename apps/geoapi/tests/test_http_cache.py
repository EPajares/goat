"""ETag revalidation for features/metadata GET endpoints.

The tag keys on (layer version, pinned snapshot, request params): any
catalog change rotates the snapshot and therefore the tag, so a 304 can
never serve data the client doesn't already have. Unpinned pools get no
ETag at all (worker-side replaces don't bump the layer version, so a
version-only tag could 304 against replaced data forever).
"""

from unittest.mock import AsyncMock, MagicMock, patch

from geoapi.http_cache import apply_cache_headers, build_query_etag, not_modified


class TestBuildQueryEtag:
    def test_none_when_unpinned(self) -> None:
        assert build_query_etag("layer1", 3, None) is None
        assert build_query_etag("layer1", 3, None, params={"limit": 10}) is None

    def test_stable_for_same_inputs(self) -> None:
        a = build_query_etag("layer1", 3, 10, params={"limit": 10, "bbox": None})
        b = build_query_etag("layer1", 3, 10, params={"limit": 10})
        assert a == b  # None params are dropped

    def test_changes_with_snapshot(self) -> None:
        assert build_query_etag("layer1", 3, 10) != build_query_etag("layer1", 3, 11)

    def test_changes_with_version_and_params(self) -> None:
        base = build_query_etag("layer1", 3, 10, params={"limit": 10})
        assert base != build_query_etag("layer1", 4, 10, params={"limit": 10})
        assert base != build_query_etag("layer1", 3, 10, params={"limit": 20})

    def test_weak_etag_format(self) -> None:
        etag = build_query_etag("layer1", 3, 10)
        assert etag is not None
        assert etag.startswith('W/"') and etag.endswith('"')


class TestNotModified:
    def test_match_returns_304_with_headers(self) -> None:
        etag = build_query_etag("layer1", 3, 10)
        resp = not_modified(etag, etag)
        assert resp is not None
        assert resp.status_code == 304
        assert resp.headers["ETag"] == etag
        assert resp.headers["Cache-Control"] == "no-cache"

    def test_mismatch_and_absent_return_none(self) -> None:
        etag = build_query_etag("layer1", 3, 10)
        assert not_modified('W/"deadbeef"', etag) is None
        assert not_modified(None, etag) is None

    def test_none_etag_never_304s(self) -> None:
        assert not_modified('W/"anything"', None) is None

    def test_apply_headers_noop_when_unpinned(self) -> None:
        response = MagicMock()
        response.headers = {}
        apply_cache_headers(response, None)
        assert response.headers == {}


class TestEndpointRevalidation:
    """End-to-end through the FastAPI app with mocked services."""

    COLLECTION = "abc123de-f456-7890-1234-5678901234ab"

    @patch("geoapi.routers.metadata.ducklake_pool")
    @patch("geoapi.routers.metadata.layer_service")
    def test_queryables_etag_roundtrip(
        self, mock_layer_service, mock_pool, test_client, sample_layer_metadata
    ) -> None:
        mock_layer_service.get_layer_metadata = AsyncMock(
            return_value=sample_layer_metadata
        )
        mock_layer_service._pool = None  # field-config lookup short-circuits
        mock_pool.pinned_snapshot_id = 42

        first = test_client.get(f"/collections/{self.COLLECTION}/queryables")
        assert first.status_code == 200
        etag = first.headers.get("etag")
        assert etag and etag.startswith('W/"')
        assert first.headers.get("cache-control") == "no-cache"

        second = test_client.get(
            f"/collections/{self.COLLECTION}/queryables",
            headers={"If-None-Match": etag},
        )
        assert second.status_code == 304
        assert second.content == b""

        # Snapshot advances (an import happened) -> revalidation misses
        mock_pool.pinned_snapshot_id = 43
        third = test_client.get(
            f"/collections/{self.COLLECTION}/queryables",
            headers={"If-None-Match": etag},
        )
        assert third.status_code == 200
        assert third.headers.get("etag") != etag

    @patch("geoapi.routers.metadata._load_field_config")
    @patch("geoapi.routers.metadata.ducklake_pool")
    @patch("geoapi.routers.metadata.layer_service")
    def test_queryables_etag_rotates_on_field_config_change(
        self,
        mock_layer_service,
        mock_pool,
        mock_load_field_config,
        test_client,
        sample_layer_metadata,
    ) -> None:
        """field_config lives in PG, not DuckLake: editing a column's
        display_config creates no snapshot and bumps no layer version, so
        the tag must key on the config itself or a 304 serves stale
        formatting forever."""
        mock_layer_service.get_layer_metadata = AsyncMock(
            return_value=sample_layer_metadata
        )
        mock_pool.pinned_snapshot_id = 42
        mock_load_field_config.return_value = {
            "value": {"kind": "number", "display_config": {"always_show_sign": False}}
        }

        first = test_client.get(f"/collections/{self.COLLECTION}/queryables")
        assert first.status_code == 200
        etag = first.headers.get("etag")
        assert etag

        # display_config edited in PG — same snapshot, same layer version
        mock_load_field_config.return_value = {
            "value": {"kind": "number", "display_config": {"always_show_sign": True}}
        }
        second = test_client.get(
            f"/collections/{self.COLLECTION}/queryables",
            headers={"If-None-Match": etag},
        )
        assert second.status_code == 200
        assert second.headers.get("etag") != etag
        assert second.json()["properties"]["value"]["display_config"] == {
            "always_show_sign": True
        }

    @patch("geoapi.routers.metadata.ducklake_pool")
    @patch("geoapi.routers.metadata.layer_service")
    def test_collection_etag_roundtrip(
        self, mock_layer_service, mock_pool, test_client, sample_layer_metadata
    ) -> None:
        mock_layer_service.get_layer_metadata = AsyncMock(
            return_value=sample_layer_metadata
        )
        mock_pool.pinned_snapshot_id = 42

        first = test_client.get(f"/collections/{self.COLLECTION}")
        assert first.status_code == 200
        etag = first.headers.get("etag")
        assert etag

        second = test_client.get(
            f"/collections/{self.COLLECTION}", headers={"If-None-Match": etag}
        )
        assert second.status_code == 304

    @patch("geoapi.routers.metadata.ducklake_pool")
    @patch("geoapi.routers.metadata.layer_service")
    def test_unpinned_pool_serves_without_etag(
        self, mock_layer_service, mock_pool, test_client, sample_layer_metadata
    ) -> None:
        """Kill-switch mode: no ETag headers, no 304s — exactly the
        pre-caching behavior."""
        mock_layer_service.get_layer_metadata = AsyncMock(
            return_value=sample_layer_metadata
        )
        mock_pool.pinned_snapshot_id = None

        first = test_client.get(f"/collections/{self.COLLECTION}")
        assert first.status_code == 200
        assert "etag" not in first.headers

        again = test_client.get(
            f"/collections/{self.COLLECTION}", headers={"If-None-Match": 'W/"x"'}
        )
        assert again.status_code == 200

    @patch("geoapi.routers.features.ducklake_pool")
    @patch("geoapi.routers.features.layer_service")
    @patch("geoapi.routers.features.feature_service")
    def test_items_304_skips_the_query_entirely(
        self,
        mock_feature_service,
        mock_layer_service,
        mock_pool,
        test_client,
        sample_layer_metadata,
    ) -> None:
        """The revalidation check runs BEFORE metadata resolution and the
        DuckLake query — a 304 must not touch either."""
        mock_layer_service.get_layer_metadata = AsyncMock(
            return_value=sample_layer_metadata
        )
        mock_feature_service.get_features_json.return_value = ('"[]"', 0, 0)
        mock_pool.pinned_snapshot_id = 42

        first = test_client.get(f"/collections/{self.COLLECTION}/items?limit=10")
        assert first.status_code == 200
        etag = first.headers.get("etag")
        assert etag
        assert mock_feature_service.get_features_json.called

        mock_feature_service.get_features_json.reset_mock()
        mock_layer_service.get_layer_metadata.reset_mock()
        second = test_client.get(
            f"/collections/{self.COLLECTION}/items?limit=10",
            headers={"If-None-Match": etag},
        )
        assert second.status_code == 304
        assert not mock_feature_service.get_features_json.called
        assert not mock_layer_service.get_layer_metadata.called

        # A different limit is a different resource -> no 304
        third = test_client.get(
            f"/collections/{self.COLLECTION}/items?limit=20",
            headers={"If-None-Match": etag},
        )
        assert third.status_code == 200
