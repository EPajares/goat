import pytest
from core.schemas.tool import IBuffer
from pydantic import ValidationError


def test_distance_step_valid():
    # Test with a valid distance step
    try:
        IBuffer(source_layer_project_id=1, max_distance=1000, distance_step=50)
    except ValidationError:
        pytest.fail("ValidationError was raised unexpectedly!")


def test_distance_step_invalid():
    # Test with an invalid distance step
    with pytest.raises(ValidationError):
        IBuffer(source_layer_project_id=1, max_distance=1000, distance_step=1)


def test_polygon_difference_valid():
    # Test with a valid polygon difference
    try:
        IBuffer(
            source_layer_project_id=1,
            max_distance=1000,
            distance_step=50,
            polygon_union=True,
            polygon_difference=True,
        )
    except ValidationError:
        pytest.fail("ValidationError was raised unexpectedly!")


def test_polygon_difference_invalid():
    # Test with an invalid polygon difference
    with pytest.raises(ValidationError):
        IBuffer(
            source_layer_project_id=1,
            max_distance=1000,
            distance_step=50,
            polygon_union=False,
            polygon_difference=True,
        )
