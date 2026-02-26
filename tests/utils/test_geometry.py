import pytest

from source.svg2excalidraw.utils.geometry import (
    bounding_dimensions,
    winding_order,
)


def test_bounding_dimensions_empty_list():
    """
    Arrange: an empty point list.
    Act: call bounding_dimensions([]).
    Assert: returns (0.0, 0.0) — degenerate/empty case yields zero dimensions.
    """
    width, height = bounding_dimensions([])
    assert width == 0.0
    assert height == 0.0


def test_bounding_dimensions_single_point():
    """
    Arrange: a list containing one point.
    Act: call bounding_dimensions with a single-element list.
    Assert: both width and height are 0.0 (a single point has no extent).
    """
    width, height = bounding_dimensions([(5.0, 10.0)])
    assert width == 0.0
    assert height == 0.0


def test_bounding_dimensions_axis_aligned_rectangle():
    """
    Arrange: four corners of a 100x50 rectangle.
    Act: call bounding_dimensions on those four points.
    Assert: width is 100.0, height is 50.0.
    """
    points = [(0.0, 0.0), (100.0, 0.0), (100.0, 50.0), (0.0, 50.0)]
    width, height = bounding_dimensions(points)
    assert width == pytest.approx(100.0)
    assert height == pytest.approx(50.0)


def test_bounding_dimensions_negative_coordinates():
    """
    Arrange: two points symmetrically placed around the origin.
    Act: call bounding_dimensions.
    Assert: width and height correctly span across negative to positive coordinates.
    """
    points = [(-10.0, -5.0), (10.0, 5.0)]
    width, height = bounding_dimensions(points)
    assert width == pytest.approx(20.0)
    assert height == pytest.approx(10.0)


def test_bounding_dimensions_only_x_varies():
    """
    Arrange: three collinear points on the same horizontal line.
    Act: call bounding_dimensions.
    Assert: height is 0.0 (no vertical extent), width spans x range.
    """
    points = [(0.0, 3.0), (10.0, 3.0), (20.0, 3.0)]
    width, height = bounding_dimensions(points)
    assert width == pytest.approx(20.0)
    assert height == pytest.approx(0.0)


def test_bounding_dimensions_fractional_values():
    """
    Arrange: points with sub-pixel fractional coordinates.
    Act: call bounding_dimensions.
    Assert: dimensions are computed exactly from the floating-point extremes.
    """
    points = [(0.5, 1.25), (3.75, 4.0)]
    width, height = bounding_dimensions(points)
    assert width == pytest.approx(3.25)
    assert height == pytest.approx(2.75)


def test_bounding_dimensions_two_identical_points():
    """
    Arrange: two points at the same location.
    Act: call bounding_dimensions.
    Assert: both dimensions are 0.0.
    """
    points = [(7.0, 7.0), (7.0, 7.0)]
    width, height = bounding_dimensions(points)
    assert width == pytest.approx(0.0)
    assert height == pytest.approx(0.0)


def test_winding_order_negative_shoelace_triangle():
    """
    Arrange: a triangle (0,0)→(10,0)→(10,10) whose shoelace sum is negative.
    Act: call winding_order.
    Assert: the function returns 'counterclockwise' for a negative-sum polygon
            (the function labels negative-shoelace polygons as 'counterclockwise').
    """
    points = [(0.0, 0.0), (10.0, 0.0), (10.0, 10.0)]
    assert winding_order(points) == "counterclockwise"


def test_winding_order_positive_shoelace_triangle():
    """
    Arrange: a triangle (0,0)→(10,10)→(10,0) whose shoelace sum is positive.
    Act: call winding_order.
    Assert: the function returns 'clockwise' for a positive-sum polygon.
    """
    points = [(0.0, 0.0), (10.0, 10.0), (10.0, 0.0)]
    assert winding_order(points) == "clockwise"


def test_winding_order_negative_shoelace_square():
    """
    Arrange: a unit square (0,0)→(1,0)→(1,1)→(0,1) — negative shoelace sum.
    Act: call winding_order.
    Assert: returns 'counterclockwise'.
    """
    points = [(0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0)]
    assert winding_order(points) == "counterclockwise"


def test_winding_order_positive_shoelace_square():
    """
    Arrange: a unit square (0,0)→(0,1)→(1,1)→(1,0) — positive shoelace sum.
    Act: call winding_order.
    Assert: returns 'clockwise'.
    """
    points = [(0.0, 0.0), (0.0, 1.0), (1.0, 1.0), (1.0, 0.0)]
    assert winding_order(points) == "clockwise"


def test_winding_order_consistent_for_reversed_polygon():
    """
    Arrange: a polygon and its vertex-reversed version.
    Act: call winding_order on both.
    Assert: they return opposite strings (reversing vertices flips winding).
    """
    forward = [(0.0, 0.0), (1000.0, 0.0), (1000.0, 1000.0)]
    backward = list(reversed(forward))
    result_forward = winding_order(forward)
    result_backward = winding_order(backward)
    assert result_forward != result_backward
