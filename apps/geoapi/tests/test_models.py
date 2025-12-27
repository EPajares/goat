"""Tests for Pydantic models."""

from geoapi.models import (
    Collection,
    Conformance,
    Extent,
    Feature,
    FeatureCollection,
    Link,
    Queryables,
    SpatialExtent,
    StyleJSON,
    TileJSON,
)


class TestLink:
    """Tests for Link model."""

    def test_link_required_fields(self):
        """Test Link with required fields only."""
        link = Link(href="https://example.com", rel="self")
        assert link.href == "https://example.com"
        assert link.rel == "self"
        assert link.type is None
        assert link.title is None

    def test_link_all_fields(self):
        """Test Link with all fields."""
        link = Link(
            href="https://example.com",
            rel="self",
            type="application/json",
            title="Example Link",
            templated=True,
        )
        assert link.type == "application/json"
        assert link.title == "Example Link"
        assert link.templated is True


class TestCollection:
    """Tests for Collection model."""

    def test_collection_minimal(self):
        """Test Collection with minimal fields."""
        collection = Collection(id="test-collection")
        assert collection.id == "test-collection"
        assert collection.title is None
        assert collection.itemType == "feature"

    def test_collection_with_extent(self):
        """Test Collection with spatial extent."""
        extent = Extent(spatial=SpatialExtent(bbox=[[-180, -90, 180, 90]]))
        collection = Collection(
            id="test-collection",
            title="Test Collection",
            extent=extent,
        )
        assert collection.extent.spatial.bbox == [[-180, -90, 180, 90]]


class TestFeature:
    """Tests for Feature model."""

    def test_feature_with_geometry(self):
        """Test Feature with geometry."""
        feature = Feature(
            id="feature-1",
            geometry={"type": "Point", "coordinates": [10.0, 52.0]},
            properties={"name": "Test Point"},
        )
        assert feature.type == "Feature"
        assert feature.id == "feature-1"
        assert feature.geometry["type"] == "Point"
        assert feature.properties["name"] == "Test Point"

    def test_feature_without_geometry(self):
        """Test Feature without geometry."""
        feature = Feature(
            id="feature-1",
            properties={"name": "No Geometry"},
        )
        assert feature.geometry is None


class TestFeatureCollection:
    """Tests for FeatureCollection model."""

    def test_empty_feature_collection(self):
        """Test empty FeatureCollection."""
        fc = FeatureCollection()
        assert fc.type == "FeatureCollection"
        assert fc.features == []
        assert fc.numberMatched is None

    def test_feature_collection_with_features(self):
        """Test FeatureCollection with features."""
        features = [
            Feature(id="1", properties={}),
            Feature(id="2", properties={}),
        ]
        fc = FeatureCollection(
            features=features,
            numberMatched=100,
            numberReturned=2,
        )
        assert len(fc.features) == 2
        assert fc.numberMatched == 100
        assert fc.numberReturned == 2


class TestTileJSON:
    """Tests for TileJSON model."""

    def test_tilejson_defaults(self):
        """Test TileJSON with default values."""
        tj = TileJSON(tiles=["https://example.com/{z}/{x}/{y}.mvt"])
        assert tj.tilejson == "3.0.0"
        assert tj.version == "1.0.0"
        assert tj.scheme == "xyz"
        assert tj.minzoom == 0
        assert tj.maxzoom == 22

    def test_tilejson_full(self):
        """Test TileJSON with all fields."""
        tj = TileJSON(
            name="Test Tiles",
            tiles=["https://example.com/{z}/{x}/{y}.mvt"],
            vector_layers=[{"id": "default", "fields": {"name": "string"}}],
            bounds=[-180, -90, 180, 90],
            center=[0, 0, 5],
            minzoom=0,
            maxzoom=14,
        )
        assert tj.name == "Test Tiles"
        assert len(tj.vector_layers) == 1
        assert tj.bounds == [-180, -90, 180, 90]


class TestStyleJSON:
    """Tests for StyleJSON model."""

    def test_stylejson_defaults(self):
        """Test StyleJSON with default values."""
        sj = StyleJSON()
        assert sj.version == 8
        assert sj.sources == {}
        assert sj.layers == []

    def test_stylejson_with_source_and_layers(self):
        """Test StyleJSON with source and layers."""
        sj = StyleJSON(
            name="Test Style",
            sources={
                "test": {
                    "type": "vector",
                    "tiles": ["https://example.com/{z}/{x}/{y}.mvt"],
                }
            },
            layers=[
                {
                    "id": "test-layer",
                    "type": "circle",
                    "source": "test",
                    "source-layer": "default",
                }
            ],
        )
        assert "test" in sj.sources
        assert len(sj.layers) == 1


class TestQueryables:
    """Tests for Queryables model."""

    def test_queryables(self):
        """Test Queryables model."""
        q = Queryables(
            title="Test Collection",
            properties={
                "name": {"name": "name", "type": "string"},
                "value": {"name": "value", "type": "number"},
            },
        )
        assert q.title == "Test Collection"
        assert q.type == "object"
        assert "name" in q.properties


class TestConformance:
    """Tests for Conformance model."""

    def test_conformance(self):
        """Test Conformance model."""
        conf = Conformance(
            conformsTo=[
                "http://www.opengis.net/spec/ogcapi-features-1/1.0/conf/core",
            ]
        )
        assert len(conf.conformsTo) == 1
