import numpy as np
import pytest
from lxml import etree

from source.svg2excalidraw.core.mapper import (
    accumulated_transform_matrix,
    parse_transform_string,
    transform_bounds,
    transform_point,
    transform_points,
)


def _approx(value: float, abs_tol: float = 1e-6) -> pytest.approx:
    return pytest.approx(value, abs=abs_tol)


def test_parse_transform_empty_string_gives_identity():
    """
    Arrange: an empty transform string.
    Act: call parse_transform_string('').
    Assert: the result is the 3x3 identity matrix.
    """
    assert np.allclose(parse_transform_string(""), np.eye(3))


def test_parse_transform_translate():
    """
    Arrange: a translate(10, 20) transform string.
    Act: apply the matrix to the origin (0, 0).
    Assert: point moves to (10, 20).
    """
    matrix = parse_transform_string("translate(10, 20)")
    x, y = transform_point(0, 0, matrix)
    assert x == _approx(10)
    assert y == _approx(20)


def test_parse_transform_translate_single_arg_defaults_y_to_zero():
    """
    Arrange: translate(5) — the single-argument form where ty defaults to 0.
    Act: apply matrix to the origin.
    Assert: point moves to (5, 0).
    """
    matrix = parse_transform_string("translate(5)")
    x, y = transform_point(0, 0, matrix)
    assert x == _approx(5)
    assert y == _approx(0)


def test_parse_transform_scale_uniform():
    """
    Arrange: scale(2) — uniform scale by factor 2.
    Act: apply matrix to point (3, 4).
    Assert: point becomes (6, 8).
    """
    matrix = parse_transform_string("scale(2)")
    x, y = transform_point(3, 4, matrix)
    assert x == _approx(6)
    assert y == _approx(8)


def test_parse_transform_scale_non_uniform():
    """
    Arrange: scale(2, 3) — different x and y scale factors.
    Act: apply matrix to point (1, 1).
    Assert: point becomes (2, 3).
    """
    matrix = parse_transform_string("scale(2, 3)")
    x, y = transform_point(1, 1, matrix)
    assert x == _approx(2)
    assert y == _approx(3)


def test_parse_transform_rotate_90_degrees():
    """
    Arrange: rotate(90).
    Act: apply matrix to point (1, 0).
    Assert: point rotates to (0, 1) (90° CW in SVG coordinates).
    """
    matrix = parse_transform_string("rotate(90)")
    x, y = transform_point(1, 0, matrix)
    assert x == _approx(0)
    assert y == _approx(1)


def test_parse_transform_rotate_180_degrees():
    """
    Arrange: rotate(180).
    Act: apply matrix to point (1, 0).
    Assert: point maps to (-1, 0).
    """
    matrix = parse_transform_string("rotate(180)")
    x, y = transform_point(1, 0, matrix)
    assert x == _approx(-1)
    assert y == _approx(0)


def test_parse_transform_rotate_around_center_point():
    """
    Arrange: rotate(90, 1, 0) — rotate 90° around (1, 0).
    Act: apply matrix to the pivot point itself (1, 0).
    Assert: the pivot is invariant under rotation about itself.
    """
    matrix = parse_transform_string("rotate(90, 1, 0)")
    x, y = transform_point(1, 0, matrix)
    assert x == _approx(1)
    assert y == _approx(0)


def test_parse_transform_skew_x():
    """
    Arrange: skewX(45) — horizontal shear by 45 degrees.
    Act: apply matrix to point (0, 1).
    Assert: x is shifted by tan(45°) * 1 = 1, y is unchanged.
    """
    matrix = parse_transform_string("skewX(45)")
    x, y = transform_point(0, 1, matrix)
    assert x == _approx(1)
    assert y == _approx(1)


def test_parse_transform_skew_y():
    """
    Arrange: skewY(45) — vertical shear by 45 degrees.
    Act: apply matrix to point (1, 0).
    Assert: y is shifted by tan(45°) * 1 = 1, x is unchanged.
    """
    matrix = parse_transform_string("skewY(45)")
    x, y = transform_point(1, 0, matrix)
    assert x == _approx(1)
    assert y == _approx(1)


def test_parse_transform_matrix_function():
    """
    Arrange: matrix(1,0,0,1,10,20) — the explicit 2D affine matrix form.
    Act: apply matrix to point (5, 5).
    Assert: point translates to (15, 25).
    """
    matrix = parse_transform_string("matrix(1,0,0,1,10,20)")
    x, y = transform_point(5, 5, matrix)
    assert x == _approx(15)
    assert y == _approx(25)


def test_parse_transform_chained_translate_then_scale():
    """
    Arrange: 'translate(10, 0) scale(2)' — SVG applies right-to-left.
    Act: apply matrix to point (1, 0).
    Assert: scale(2) first gives 2, then translate(10) gives 12.
    """
    matrix = parse_transform_string("translate(10, 0) scale(2)")
    x, y = transform_point(1, 0, matrix)
    assert x == _approx(12)
    assert y == _approx(0)


def test_parse_transform_chained_scale_then_translate():
    """
    Arrange: 'scale(2) translate(10,0)' — translate first in SVG order.
    Act: apply matrix to origin (0, 0).
    Assert: translate(10) moves 0→10, scale(2) then doubles to 20.
    """
    matrix = parse_transform_string("scale(2) translate(10, 0)")
    x, y = transform_point(0, 0, matrix)
    assert x == _approx(20)
    assert y == _approx(0)


def test_transform_points_applies_to_each_point():
    """
    Arrange: two points and a translate(1, 2) matrix.
    Act: call transform_points.
    Assert: both points are shifted by (1, 2).
    """
    matrix = parse_transform_string("translate(1, 2)")
    result = transform_points([(0.0, 0.0), (3.0, 4.0)], matrix)
    assert result[0] == (_approx(1), _approx(2))
    assert result[1] == (_approx(4), _approx(6))


def test_transform_points_empty_list():
    """
    Arrange: an empty point list.
    Act: call transform_points.
    Assert: the result is an empty list.
    """
    assert transform_points([], np.eye(3)) == []


def test_transform_bounds_identity_matrix():
    """
    Arrange: a bounding box (10, 20, width=100, height=50) and the identity matrix.
    Act: call transform_bounds.
    Assert: origin and dimensions are unchanged.
    """
    x, y, w, h = transform_bounds(10, 20, 100, 50, np.eye(3))
    assert (x, y, w, h) == (_approx(10), _approx(20), _approx(100), _approx(50))


def test_transform_bounds_translation():
    """
    Arrange: a bounding box at the origin with size 100x50 and translate(5, 10).
    Act: call transform_bounds.
    Assert: origin shifts to (5, 10) while dimensions stay the same.
    """
    matrix = parse_transform_string("translate(5, 10)")
    x, y, w, h = transform_bounds(0, 0, 100, 50, matrix)
    assert x == _approx(5)
    assert y == _approx(10)
    assert w == _approx(100)
    assert h == _approx(50)


def test_transform_bounds_scale_doubles_everything():
    """
    Arrange: a bounding box at (10, 20) with size 100x50 and scale(2).
    Act: call transform_bounds.
    Assert: both origin and dimensions are doubled.
    """
    matrix = parse_transform_string("scale(2)")
    x, y, w, h = transform_bounds(10, 20, 100, 50, matrix)
    assert x == _approx(20)
    assert y == _approx(40)
    assert w == _approx(200)
    assert h == _approx(100)


def test_transform_bounds_rotate_90_swaps_width_and_height():
    """
    Arrange: an axis-aligned bounding box of 100x50 and a 90-degree rotation.
    Act: call transform_bounds.
    Assert: after rotation, the new bounding width ≈ 50 and height ≈ 100.
    """
    matrix = parse_transform_string("rotate(90)")
    _, _, w, h = transform_bounds(0, 0, 100, 50, matrix)
    assert w == _approx(50, abs_tol=1e-4)
    assert h == _approx(100, abs_tol=1e-4)


def test_accumulated_matrix_no_groups_uses_element_transform():
    """
    Arrange: a rect with transform='translate(5, 10)' and an empty group list.
    Act: call accumulated_transform_matrix.
    Assert: result is equivalent to the element's own translate transform.
    """
    element = etree.fromstring('<rect transform="translate(5, 10)"/>')
    matrix = accumulated_transform_matrix(element, [])
    x, y = transform_point(0, 0, matrix)
    assert x == _approx(5)
    assert y == _approx(10)


def test_accumulated_matrix_element_with_no_transform():
    """
    Arrange: a rect with no transform and an empty group list.
    Act: call accumulated_transform_matrix.
    Assert: result is the identity matrix (no displacement).
    """
    element = etree.fromstring("<rect/>")
    matrix = accumulated_transform_matrix(element, [])
    assert np.allclose(matrix, np.eye(3))


def test_accumulated_matrix_two_groups_accumulate():
    """
    Arrange: two group elements translating by (10, 0) and (0, 20) respectively.
    Act: call accumulated_transform_matrix on a plain rect with both groups.
    Assert: total translation is (10, 20).
    """
    group_1 = etree.fromstring('<g transform="translate(10, 0)"/>')
    group_2 = etree.fromstring('<g transform="translate(0, 20)"/>')
    element = etree.fromstring("<rect/>")
    matrix = accumulated_transform_matrix(element, [group_1, group_2])
    x, y = transform_point(0, 0, matrix)
    assert x == _approx(10)
    assert y == _approx(20)


def test_accumulated_matrix_group_and_element():
    """
    Arrange: a group translating (5, 0) and an element translating (0, 3).
    Act: call accumulated_transform_matrix.
    Assert: combined translation is (5, 3).
    """
    group = etree.fromstring('<g transform="translate(5, 0)"/>')
    element = etree.fromstring('<rect transform="translate(0, 3)"/>')
    matrix = accumulated_transform_matrix(element, [group])
    x, y = transform_point(0, 0, matrix)
    assert x == _approx(5)
    assert y == _approx(3)


def test_accumulated_matrix_group_with_no_transform():
    """
    Arrange: a group element with no transform attribute.
    Act: call accumulated_transform_matrix on a child rect that also has no transform.
    Assert: result is the identity matrix.
    """
    group = etree.fromstring("<g/>")
    element = etree.fromstring("<rect/>")
    matrix = accumulated_transform_matrix(element, [group])
    assert np.allclose(matrix, np.eye(3))
