import pytest
from core.schemas.toolbox_base import (
    CatchmentAreaStartingPointsBase,
    FeatureGeometryType,
    InputLayerType,
    LayerType,
)
from pydantic import ValidationError


def test_catchment_area_starting_points_base_both_coords_and_layer_id():
    # Test that providing both coordinates and layer_project_id raises a ValidationError
    with pytest.raises(ValidationError):
        CatchmentAreaStartingPointsBase(latitude=[0.0], longitude=[0.0], layer_project_id=1)

def test_catchment_area_starting_points_base_coords_length_mismatch():
    # Test that providing latitude and longitude of different lengths raises a ValidationError
    with pytest.raises(ValidationError):
        CatchmentAreaStartingPointsBase(latitude=[0.0], longitude=[0.0, 1.0])

def test_catchment_area_starting_points_base_coords_out_of_bounds():
    # Test that providing latitude and/or longitude out of bounds raises a ValidationError
    with pytest.raises(ValidationError):
        CatchmentAreaStartingPointsBase(latitude=[-91.0], longitude=[0.0])
    with pytest.raises(ValidationError):
        CatchmentAreaStartingPointsBase(latitude=[0.0], longitude=[-181.0])

def test_catchment_area_starting_points_base_no_coords_or_layer_id():
    # Test that not providing either coordinates or layer_project_id raises a ValidationError
    with pytest.raises(ValidationError):
        CatchmentAreaStartingPointsBase(latitude=None, longitude=None, layer_project_id=None)

def test_catchment_area_starting_points_base_valid_input():
    # Test that valid input does not raise a ValidationError
    CatchmentAreaStartingPointsBase(latitude=[0.0], longitude=[0.0])
    CatchmentAreaStartingPointsBase(layer_project_id=1)

def test_input_layer_type_feature_layer():
    # Test that when layer_type is feature, feature_layer_geometry_types cannot be null
    with pytest.raises(ValidationError):
        InputLayerType(layer_types=[LayerType.feature.value], feature_layer_geometry_types=None)

def test_input_layer_type_table_layer():
    # Test that when layer_type is table, feature_layer_geometry_types must be null
    with pytest.raises(ValidationError):
        InputLayerType(layer_types=[LayerType.table.value], feature_layer_geometry_types=[FeatureGeometryType.point.value])

def test_input_layer_type_invalid_layer():
    # Test that an invalid layer_type raises a ValidationError
    with pytest.raises(ValidationError):
        InputLayerType(layer_types=["invalid_layer"], feature_layer_geometry_types=None)

def test_input_layer_type_no_layers():
    # Test that layer_type cannot be none
    with pytest.raises(ValidationError):
        InputLayerType(layer_types=[], feature_layer_geometry_types=None)
