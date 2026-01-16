"""Tests for tile service including PMTiles support."""

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from geoapi.services.tile_service import (
    TileService,
    tile_to_bbox_3857,
    tile_to_bbox_4326,
)

# =====================================================================
#  Coordinate Conversion Tests
# =====================================================================


def test_tile_to_bbox_4326_z0() -> None:
    """Test bbox for world tile at z=0."""
    bbox = tile_to_bbox_4326(0, 0, 0)
    assert bbox[0] == pytest.approx(-180.0)
    assert bbox[2] == pytest.approx(180.0)
    # Y bounds are clamped by Web Mercator
    assert bbox[1] < -80
    assert bbox[3] > 80


def test_tile_to_bbox_4326_z1() -> None:
    """Test bbox for tiles at z=1."""
    # Top-left tile (NW hemisphere)
    bbox = tile_to_bbox_4326(1, 0, 0)
    assert bbox[0] == pytest.approx(-180.0)
    assert bbox[2] == pytest.approx(0.0)
    assert bbox[3] > 0  # Northern hemisphere


def test_tile_to_bbox_3857() -> None:
    """Test Web Mercator bbox calculation."""
    bbox = tile_to_bbox_3857(0, 0, 0)
    # Full Web Mercator extent
    assert bbox[0] == pytest.approx(-20037508.342789244)
    assert bbox[2] == pytest.approx(20037508.342789244)


def test_tile_to_bbox_3857_higher_zoom() -> None:
    """Test Web Mercator bbox at higher zoom levels."""
    # At z=1, each tile is half the extent
    bbox_nw = tile_to_bbox_3857(1, 0, 0)  # Northwest tile
    bbox_se = tile_to_bbox_3857(1, 1, 1)  # Southeast tile

    # NW tile should be in negative x, positive y
    assert bbox_nw[0] < 0
    assert bbox_nw[3] > 0

    # SE tile should be in positive x, negative y
    assert bbox_se[2] > 0
    assert bbox_se[1] < 0


# =====================================================================
#  TileService Tests
# =====================================================================


def test_tile_service_init() -> None:
    """Test TileService initialization."""
    service = TileService()
    assert hasattr(service, "_pmtiles_exists_cache")
    assert isinstance(service._pmtiles_exists_cache, dict)


def test_should_use_pmtiles_with_filter() -> None:
    """Test that filters disable PMTiles usage."""
    service = TileService()
    layer_info = MagicMock()
    layer_info.schema_name = "user_test"
    layer_info.table_name = "t_layer"

    # With CQL filter - should not use PMTiles
    result = service._should_use_pmtiles(
        layer_info, cql_filter={"filter": "value > 10", "lang": "cql2-json"}
    )
    assert result is False

    # With bbox filter - should not use PMTiles
    result = service._should_use_pmtiles(layer_info, bbox=[0, 0, 1, 1])
    assert result is False


def test_should_use_pmtiles_no_file() -> None:
    """Test that missing PMTiles file returns False."""
    with tempfile.TemporaryDirectory() as tmpdir:
        with patch.object(
            TileService,
            "_get_pmtiles_path",
            return_value=Path(tmpdir) / "missing.pmtiles",
        ):
            service = TileService()
            layer_info = MagicMock()
            layer_info.schema_name = "user_test"
            layer_info.table_name = "t_layer"

            result = service._should_use_pmtiles(layer_info)
            assert result is False


def test_invalidate_pmtiles_cache() -> None:
    """Test cache invalidation for a specific layer."""
    service = TileService()

    # Add mock entry to cache
    service._pmtiles_exists_cache["user_test/t_layer"] = True

    # Invalidate
    service.invalidate_pmtiles_cache("user_test", "t_layer")

    # Verify removed
    assert "user_test/t_layer" not in service._pmtiles_exists_cache


def test_invalidate_all_pmtiles_cache() -> None:
    """Test clearing entire cache."""
    service = TileService()

    # Add multiple mock entries
    service._pmtiles_exists_cache["layer1"] = True
    service._pmtiles_exists_cache["layer2"] = False

    # Invalidate all
    service.invalidate_all_pmtiles_cache()

    # Verify all removed
    assert len(service._pmtiles_exists_cache) == 0


def test_pmtiles_exists_caching() -> None:
    """Test that PMTiles existence check is cached."""
    with tempfile.TemporaryDirectory() as tmpdir:
        pmtiles_path = Path(tmpdir) / "test.pmtiles"

        with patch.object(
            TileService,
            "_get_pmtiles_path",
            return_value=pmtiles_path,
        ):
            service = TileService()
            layer_info = MagicMock()
            layer_info.schema_name = "user_test"
            layer_info.table_name = "t_layer"

            # First call - file doesn't exist
            assert service._pmtiles_exists(layer_info) is False
            assert "user_test/t_layer" in service._pmtiles_exists_cache

            # Create the file
            pmtiles_path.touch()

            # Second call - should still return cached False
            assert service._pmtiles_exists(layer_info) is False

            # Invalidate cache
            service.invalidate_pmtiles_cache("user_test", "t_layer")

            # Third call - should now find the file
            assert service._pmtiles_exists(layer_info) is True


def test_get_pmtiles_path() -> None:
    """Test PMTiles path construction."""
    service = TileService()
    layer_info = MagicMock()
    layer_info.schema_name = "user_abc123"
    layer_info.table_name = "t_layer456"

    path = service._get_pmtiles_path(layer_info)

    assert path.name == "t_layer456.pmtiles"
    assert "tiles" in str(path)
    assert "user_abc123" in str(path)


@pytest.mark.asyncio
async def test_get_tile_from_pmtiles_missing_file() -> None:
    """Test that missing PMTiles file returns None."""
    with tempfile.TemporaryDirectory() as tmpdir:
        with patch.object(
            TileService,
            "_get_pmtiles_path",
            return_value=Path(tmpdir) / "missing.pmtiles",
        ):
            service = TileService()
            layer_info = MagicMock()
            layer_info.schema_name = "user_test"
            layer_info.table_name = "t_layer"

            result = await service._get_tile_from_pmtiles(layer_info, 0, 0, 0)
            assert result is None
