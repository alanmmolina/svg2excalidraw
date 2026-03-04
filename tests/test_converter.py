import json

import pytest

from source.svg2excalidraw.converter import convert


def _svg(inner: str, view_box: str = "0 0 200 200") -> str:
    return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{view_box}">{inner}</svg>'


def _elements(svg_string: str) -> list[dict]:
    return convert(svg_string)["elements"]


def _first_of_type(svg_string: str, element_type: str) -> dict:
    matches = [e for e in _elements(svg_string) if e["type"] == element_type]
    assert matches, f"No element of type '{element_type}' in output"
    return matches[0]


def _approx(value: float, tol: float = 0.5) -> pytest.approx:
    return pytest.approx(value, abs=tol)


@pytest.fixture
def empty_svg():
    return _svg("")


@pytest.fixture
def simple_rect_svg():
    return _svg('<rect x="10" y="20" width="100" height="50"/>')


def test_convert_returns_dict():
    """
    Arrange: a minimal empty SVG string.
    Act: call convert().
    Assert: the return value is a dict.
    """
    result = convert(_svg(""))
    assert isinstance(result, dict)


def test_convert_has_required_top_level_keys(empty_svg):
    """
    Arrange: an empty SVG.
    Act: call convert().
    Assert: keys 'type', 'version', 'elements', 'appState', 'files' are all present.
    """
    result = convert(empty_svg)
    for key in ("type", "version", "elements", "appState", "files"):
        assert key in result


def test_convert_type_is_excalidraw(empty_svg):
    """
    Arrange: an empty SVG.
    Act: call convert() and read 'type'.
    Assert: equals 'excalidraw'.
    """
    assert convert(empty_svg)["type"] == "excalidraw"


def test_convert_version_is_2(empty_svg):
    """
    Arrange: an empty SVG.
    Act: call convert() and read 'version'.
    Assert: equals 2.
    """
    assert convert(empty_svg)["version"] == 2


def test_convert_empty_svg_produces_no_elements(empty_svg):
    """
    Arrange: a valid SVG with no shapes.
    Act: call convert().
    Assert: 'elements' list is empty.
    """
    assert _elements(empty_svg) == []


def test_convert_as_json_flag_returns_string(empty_svg):
    """
    Arrange: a valid empty SVG.
    Act: call convert(svg, as_json=True).
    Assert: the return value is a string (not a dict).
    """
    result = convert(empty_svg, as_json=True)
    assert isinstance(result, str)


def test_convert_as_json_output_is_valid_json(empty_svg):
    """
    Arrange: a valid empty SVG.
    Act: call convert with as_json=True and parse with json.loads.
    Assert: no exception raised and result has 'type' == 'excalidraw'.
    """
    result = json.loads(convert(empty_svg, as_json=True))
    assert result["type"] == "excalidraw"


def test_convert_invalid_xml_raises_value_error():
    """
    Arrange: a string that is not valid XML.
    Act: call convert() on it.
    Assert: ValueError is raised with a message mentioning 'Invalid SVG'.
    """
    with pytest.raises(ValueError, match="Invalid SVG"):
        convert("this is not xml !@#")


def test_convert_incomplete_xml_raises_value_error():
    """
    Arrange: a truncated XML string that is not well-formed.
    Act: call convert().
    Assert: ValueError is raised.
    """
    with pytest.raises(ValueError):
        convert("<svg><rect")


def test_rect_produces_rectangle_type():
    """
    Arrange: an SVG containing a single rect element.
    Act: call convert() and find the rectangle element.
    Assert: the element type is 'rectangle'.
    """
    element = _first_of_type(_svg('<rect x="0" y="0" width="10" height="10"/>'), "rectangle")
    assert element["type"] == "rectangle"


def test_rect_position(simple_rect_svg):
    """
    Arrange: a rect at x=10, y=20.
    Act: call convert() and retrieve the rectangle.
    Assert: x ≈ 10, y ≈ 20.
    """
    element = _first_of_type(simple_rect_svg, "rectangle")
    assert element["x"] == _approx(10)
    assert element["y"] == _approx(20)


def test_rect_dimensions(simple_rect_svg):
    """
    Arrange: a rect with width=100, height=50.
    Act: call convert().
    Assert: width ≈ 100, height ≈ 50.
    """
    element = _first_of_type(simple_rect_svg, "rectangle")
    assert element["width"] == _approx(100)
    assert element["height"] == _approx(50)


def test_rect_fill_color():
    """
    Arrange: a rect with fill='#ff0000'.
    Act: call convert().
    Assert: 'backgroundColor' is '#ff0000'.
    """
    element = _first_of_type(
        _svg('<rect x="0" y="0" width="10" height="10" fill="#ff0000"/>'),
        "rectangle",
    )
    assert element["backgroundColor"] == "#ff0000"


def test_rect_stroke_color():
    """
    Arrange: a rect with stroke='#0000ff'.
    Act: call convert().
    Assert: 'strokeColor' is '#0000ff'.
    """
    element = _first_of_type(
        _svg('<rect x="0" y="0" width="10" height="10" stroke="#0000ff"/>'),
        "rectangle",
    )
    assert element["strokeColor"] == "#0000ff"


def test_rect_with_rx_gets_round_sharpness():
    """
    Arrange: a rect with rx='5' (rounded corners).
    Act: call convert().
    Assert: 'strokeSharpness' is 'round'.
    """
    element = _first_of_type(_svg('<rect x="0" y="0" width="10" height="10" rx="5"/>'), "rectangle")
    assert element["strokeSharpness"] == "round"


def test_rect_without_rx_keeps_sharp_sharpness():
    """
    Arrange: a rect with no rx attribute.
    Act: call convert().
    Assert: 'strokeSharpness' is 'sharp'.
    """
    element = _first_of_type(_svg('<rect x="0" y="0" width="10" height="10"/>'), "rectangle")
    assert element["strokeSharpness"] == "sharp"


def test_rect_with_ry_also_gets_round_sharpness():
    """
    Arrange: a rect with ry (but not rx) set.
    Act: call convert().
    Assert: 'strokeSharpness' is 'round' (ry also triggers rounding).
    """
    element = _first_of_type(_svg('<rect x="0" y="0" width="10" height="10" ry="3"/>'), "rectangle")
    assert element["strokeSharpness"] == "round"


def test_rect_with_transform_applies_translation():
    """
    Arrange: a rect at (0,0) with transform='translate(50, 30)'.
    Act: call convert().
    Assert: the rectangle's x ≈ 50, y ≈ 30.
    """
    element = _first_of_type(
        _svg('<rect x="0" y="0" width="10" height="10" transform="translate(50, 30)"/>'),
        "rectangle",
    )
    assert element["x"] == _approx(50)
    assert element["y"] == _approx(30)


def test_rect_output_uses_camel_case_keys():
    """
    Arrange: a styled rect element.
    Act: call convert().
    Assert: camelCase keys like 'strokeColor' are present; snake_case keys are absent.
    """
    element = _first_of_type(
        _svg('<rect x="0" y="0" width="10" height="10" fill="red"/>'),
        "rectangle",
    )
    assert "backgroundColor" in element
    assert "strokeColor" in element
    assert "background_color" not in element


def test_circle_becomes_ellipse_type():
    """
    Arrange: an SVG circle element.
    Act: call convert().
    Assert: Excalidraw output uses type 'ellipse' (circles map to ellipses).
    """
    element = _first_of_type(_svg('<circle cx="50" cy="50" r="30"/>'), "ellipse")
    assert element["type"] == "ellipse"


def test_circle_x_is_center_minus_radius():
    """
    Arrange: circle at cx=50, cy=50, r=30.
    Act: call convert().
    Assert: x ≈ cx - r = 20, y ≈ cy - r = 20.
    """
    element = _first_of_type(_svg('<circle cx="50" cy="50" r="30"/>'), "ellipse")
    assert element["x"] == _approx(20)
    assert element["y"] == _approx(20)


def test_circle_width_and_height_are_diameter():
    """
    Arrange: circle with r=30.
    Act: call convert().
    Assert: width ≈ 60, height ≈ 60 (diameter = 2r).
    """
    element = _first_of_type(_svg('<circle cx="50" cy="50" r="30"/>'), "ellipse")
    assert element["width"] == _approx(60)
    assert element["height"] == _approx(60)


def test_ellipse_type():
    """
    Arrange: an SVG ellipse element.
    Act: call convert().
    Assert: element type is 'ellipse'.
    """
    assert (
        _first_of_type(_svg('<ellipse cx="60" cy="40" rx="50" ry="20"/>'), "ellipse")["type"]
        == "ellipse"
    )


def test_ellipse_position():
    """
    Arrange: ellipse at cx=60, cy=40, rx=50, ry=20.
    Act: call convert().
    Assert: x ≈ cx - rx = 10, y ≈ cy - ry = 20.
    """
    element = _first_of_type(_svg('<ellipse cx="60" cy="40" rx="50" ry="20"/>'), "ellipse")
    assert element["x"] == _approx(10)
    assert element["y"] == _approx(20)


def test_ellipse_dimensions():
    """
    Arrange: ellipse with rx=50, ry=20.
    Act: call convert().
    Assert: width ≈ 100 (2*rx), height ≈ 40 (2*ry).
    """
    element = _first_of_type(_svg('<ellipse cx="60" cy="40" rx="50" ry="20"/>'), "ellipse")
    assert element["width"] == _approx(100)
    assert element["height"] == _approx(40)


def test_line_type():
    """
    Arrange: an SVG line element.
    Act: call convert().
    Assert: element type is 'line'.
    """
    assert _first_of_type(_svg('<line x1="0" y1="0" x2="100" y2="0"/>'), "line")["type"] == "line"


def test_line_has_two_points():
    """
    Arrange: a line from (0,0) to (100,0).
    Act: call convert().
    Assert: 'points' list contains exactly 2 entries.
    """
    element = _first_of_type(_svg('<line x1="0" y1="0" x2="100" y2="0"/>'), "line")
    assert len(element["points"]) == 2


def test_line_first_point_is_origin():
    """
    Arrange: a line from (10,20) to (110,20).
    Act: call convert().
    Assert: first point in 'points' is [0, 0] (relative coordinates start at origin).
    """
    element = _first_of_type(_svg('<line x1="10" y1="20" x2="110" y2="20"/>'), "line")
    assert element["points"][0] == [_approx(0), _approx(0)]


def test_line_second_point_is_relative_offset():
    """
    Arrange: a horizontal line from (10,20) to (110,20).
    Act: call convert().
    Assert: second point is [100, 0] — offset from the first point.
    """
    element = _first_of_type(_svg('<line x1="10" y1="20" x2="110" y2="20"/>'), "line")
    assert element["points"][1] == [_approx(100), _approx(0)]


def test_polyline_type():
    """
    Arrange: a polyline with three vertices.
    Act: call convert().
    Assert: element type is 'line'.
    """
    assert _first_of_type(_svg('<polyline points="0,0 100,0 100,100"/>'), "line")["type"] == "line"


def test_polyline_point_count():
    """
    Arrange: a polyline with 3 vertices (open — no fill).
    Act: call convert().
    Assert: 'points' has exactly 3 entries.
    """
    element = _first_of_type(_svg('<polyline points="0,0 100,0 100,100"/>'), "line")
    assert len(element["points"]) == 3


def test_polygon_last_point_closes_shape():
    """
    Arrange: a polygon with 3 vertices.
    Act: call convert().
    Assert: the last point in 'points' equals [0, 0] (closure back to the first vertex).
    """
    element = _first_of_type(_svg('<polygon points="0,0 100,0 100,100"/>'), "line")
    assert element["points"][-1] == [_approx(0), _approx(0)]


def test_polygon_point_count_includes_closure():
    """
    Arrange: a polygon with 3 vertices.
    Act: call convert().
    Assert: 'points' has 4 entries (3 vertices + 1 closing point).
    """
    element = _first_of_type(_svg('<polygon points="0,0 100,0 100,100"/>'), "line")
    assert len(element["points"]) == 4


def test_group_transform_applied_to_child():
    """
    Arrange: a group with translate(50,50) containing a rect at (0,0).
    Act: call convert().
    Assert: the rect's x ≈ 50, y ≈ 50.
    """
    element = _first_of_type(
        _svg('<g transform="translate(50, 50)"><rect x="0" y="0" width="10" height="10"/></g>'),
        "rectangle",
    )
    assert element["x"] == _approx(50)
    assert element["y"] == _approx(50)


def test_nested_group_transforms_accumulate():
    """
    Arrange: two nested groups with translate(10,0) and translate(0,20), each containing a rect.
    Act: call convert().
    Assert: the rect is at x ≈ 10, y ≈ 20 (transforms compose).
    """
    element = _first_of_type(
        _svg(
            '<g transform="translate(10, 0)">'
            '<g transform="translate(0, 20)">'
            '<rect x="0" y="0" width="5" height="5"/>'
            "</g></g>"
        ),
        "rectangle",
    )
    assert element["x"] == _approx(10)
    assert element["y"] == _approx(20)


def test_siblings_in_group_share_group_id():
    """
    Arrange: a group containing two sibling elements.
    Act: call convert() and inspect groupIds for both elements.
    Assert: both elements share the same groupId.
    """
    elements = _elements(
        _svg('<g><rect x="0" y="0" width="5" height="5"/><circle cx="10" cy="10" r="5"/></g>')
    )
    assert len(elements) == 2
    assert elements[0]["groupIds"] == elements[1]["groupIds"]
    assert len(elements[0]["groupIds"]) >= 1


def test_group_fill_inherited_by_child():
    """
    Arrange: a group with fill='#aabbcc' containing a rect with no fill.
    Act: call convert().
    Assert: the rect inherits backgroundColor='#aabbcc' from the group.
    """
    element = _first_of_type(
        _svg('<g fill="#aabbcc"><rect x="0" y="0" width="10" height="10"/></g>'),
        "rectangle",
    )
    assert element["backgroundColor"] == "#aabbcc"


def test_ungrouped_element_has_empty_group_ids():
    """
    Arrange: a rect with no enclosing group.
    Act: call convert().
    Assert: 'groupIds' is an empty list.
    """
    element = _first_of_type(_svg('<rect x="0" y="0" width="10" height="10"/>'), "rectangle")
    assert element["groupIds"] == []


def test_path_produces_line_elements():
    """
    Arrange: a simple open SVG path with two line segments.
    Act: call convert().
    Assert: at least one element of type 'line' is returned.
    """
    elements = _elements(_svg('<path d="M 10 10 L 50 10 L 50 50"/>'))
    assert len(elements) >= 1
    assert all(e["type"] == "line" for e in elements)


def test_path_origin_matches_first_move():
    """
    Arrange: a path starting at M 20 30.
    Act: call convert() and take the first element.
    Assert: element x ≈ 20, y ≈ 30.
    """
    element = _elements(_svg('<path d="M 20 30 L 80 30"/>'))[0]
    assert element["x"] == _approx(20)
    assert element["y"] == _approx(30)


def test_closed_path_last_point_returns_to_start():
    """
    Arrange: a closed path 'M 0 0 L 100 0 L 100 100 Z'.
    Act: call convert() and check the last point.
    Assert: the last point in 'points' is [0, 0] (Z closes the path).
    """
    element = _elements(_svg('<path d="M 0 0 L 100 0 L 100 100 Z"/>'))[0]
    assert element["points"][-1] == [_approx(0), _approx(0)]


def test_multi_subpath_produces_multiple_elements():
    """
    Arrange: a path string with two sub-paths (two M commands).
    Act: call convert().
    Assert: two elements are returned, one per sub-path.
    """
    elements = _elements(_svg('<path d="M 0 0 L 10 10 M 20 20 L 30 30"/>'))
    assert len(elements) == 2


def test_path_with_empty_d_adds_nothing():
    """
    Arrange: a path element with an empty d attribute.
    Act: call convert().
    Assert: no elements are added to the scene.
    """
    assert _elements(_svg('<path d=""/>')) == []
