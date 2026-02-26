import pytest

from source.svg2excalidraw.core.tracer import trace


def test_simple_move_and_line_produces_one_subpath():
    """
    Arrange: a path with a single Move and one Line command: 'M 0 0 L 10 10'.
    Act: call trace.
    Assert: exactly one subpath is returned.
    """
    result = trace("M 0 0 L 10 10")
    assert len(result) == 1


def test_simple_move_and_line_produces_two_points():
    """
    Arrange: 'M 0 0 L 10 10' — a path with start and one endpoint.
    Act: call trace.
    Assert: the single subpath contains exactly 2 points.
    """
    result = trace("M 0 0 L 10 10")
    assert len(result[0]) == 2


def test_start_point_matches_move_coordinates():
    """
    Arrange: 'M 5 7 L 20 20'.
    Act: call trace.
    Assert: the first point in the subpath is (5.0, 7.0).
    """
    result = trace("M 5 7 L 20 20")
    first_point = result[0][0]
    assert first_point == pytest.approx((5.0, 7.0), abs=1e-3)


def test_endpoint_matches_line_destination():
    """
    Arrange: 'M 0 0 L 100 50'.
    Act: call trace.
    Assert: the last point in the subpath is approximately (100, 50).
    """
    result = trace("M 0 0 L 100 50")
    last_point = result[0][-1]
    assert last_point[0] == pytest.approx(100.0, abs=1e-3)
    assert last_point[1] == pytest.approx(50.0, abs=1e-3)


def test_closed_path_repeats_start_as_final_point():
    """
    Arrange: 'M 0 0 L 10 0 L 10 10 Z' — a closed triangle.
    Act: call trace.
    Assert: the last point in the subpath equals the first point (closure).
    """
    result = trace("M 0 0 L 10 0 L 10 10 Z")
    subpath = result[0]
    assert subpath[0] == subpath[-1]


def test_closed_path_has_start_back_as_extra_point():
    """
    Arrange: 'M 0 0 L 10 0 L 10 10 Z' — a three-segment triangle closed with Z.
    Act: call trace.
    Assert: subpath length is 4 (start + 2 line endpoints + closing duplicate of start).
    """
    result = trace("M 0 0 L 10 0 L 10 10 Z")
    assert len(result[0]) == 4


def test_two_move_commands_produce_two_subpaths():
    """
    Arrange: 'M 0 0 L 5 5 M 20 20 L 30 30' — two disjoint sub-paths.
    Act: call trace.
    Assert: exactly two subpaths are returned.
    """
    result = trace("M 0 0 L 5 5 M 20 20 L 30 30")
    assert len(result) == 2


def test_second_subpath_starts_at_second_move():
    """
    Arrange: 'M 0 0 L 5 5 M 20 20 L 30 30'.
    Act: call trace and check the second subpath.
    Assert: the second subpath's first point is approximately (20, 20).
    """
    result = trace("M 0 0 L 5 5 M 20 20 L 30 30")
    second_start = result[1][0]
    assert second_start[0] == pytest.approx(20.0, abs=1e-3)
    assert second_start[1] == pytest.approx(20.0, abs=1e-3)


def test_cubic_bezier_is_sampled_into_multiple_points():
    """
    Arrange: a path containing a cubic Bezier curve 'C'.
    Act: call trace with default curve_samples=20.
    Assert: the subpath contains considerably more points than just start + end
            (the curve was sampled, not represented as two endpoints only).
    """
    result = trace("M 0 0 C 0 50 100 50 100 0")
    # With 20 samples + 1 start point there should be 21 points
    assert len(result[0]) >= 20


def test_custom_curve_samples_changes_point_count():
    """
    Arrange: the same cubic Bezier path.
    Act: call trace with curve_samples=5.
    Assert: the subpath contains exactly 6 points (1 Move + 5 samples).
    """
    result = trace("M 0 0 C 0 50 100 50 100 0", curve_samples=5)
    assert len(result[0]) == 6


def test_invalid_path_data_returns_empty_list():
    """
    Arrange: a string that is not a valid SVG path.
    Act: call trace.
    Assert: an empty list is returned (no crash).
    """
    result = trace("NOT A PATH ☠")
    assert result == []


def test_empty_path_string_returns_empty_list():
    """
    Arrange: an empty string.
    Act: call trace.
    Assert: an empty list is returned.
    """
    result = trace("")
    assert result == []


def test_path_with_only_move_command():
    """
    Arrange: 'M 10 10' — a path that only moves but draws nothing.
    Act: call trace.
    Assert: one subpath is returned with a single point (the move destination).
    """
    result = trace("M 10 10")
    assert len(result) == 1
    assert len(result[0]) == 1
