import pytest

from source.svg2excalidraw.models.elements import (
    build_ellipse,
    build_line,
    build_rectangle,
    build_text,
)


@pytest.fixture
def rect():
    return build_rectangle(x=10.0, y=20.0, width=100.0, height=50.0)


@pytest.fixture
def line_element():
    return build_line(
        x=0.0,
        y=0.0,
        width=100.0,
        height=0.0,
        points=[[0.0, 0.0], [100.0, 0.0]],
    )


def test_build_rectangle_type_field():
    """
    Arrange: nothing.
    Act: create a rectangle via build_rectangle().
    Assert: the 'type' field is 'rectangle'.
    """
    element = build_rectangle()
    assert element.type == "rectangle"


def test_build_ellipse_type_field():
    """
    Arrange: nothing.
    Act: create an ellipse via build_ellipse().
    Assert: the 'type' field is 'ellipse'.
    """
    element = build_ellipse()
    assert element.type == "ellipse"


def test_build_line_type_field():
    """
    Arrange: nothing.
    Act: create a line via build_line().
    Assert: the 'type' field is 'line'.
    """
    element = build_line()
    assert element.type == "line"


def test_element_default_stroke_color():
    """
    Arrange: nothing.
    Act: create a rectangle with no overrides.
    Assert: stroke_color defaults to '#000000'.
    """
    element = build_rectangle()
    assert element.stroke_color == "#000000"


def test_element_default_background_color():
    """
    Arrange: nothing.
    Act: create a rectangle with no overrides.
    Assert: background_color defaults to 'transparent'.
    """
    element = build_rectangle()
    assert element.background_color == "transparent"


def test_element_default_opacity():
    """
    Arrange: nothing.
    Act: create a rectangle with no overrides.
    Assert: opacity defaults to 100.
    """
    element = build_rectangle()
    assert element.opacity == 100


def test_element_default_roughness():
    """
    Arrange: nothing.
    Act: create a rectangle with no overrides.
    Assert: roughness defaults to 0.
    """
    element = build_rectangle()
    assert element.roughness == 0


def test_element_default_stroke_sharpness():
    """
    Arrange: nothing.
    Act: create a rectangle with no overrides.
    Assert: stroke_sharpness defaults to 'sharp'.
    """
    element = build_rectangle()
    assert element.stroke_sharpness == "sharp"


def test_element_default_group_ids_is_empty_list():
    """
    Arrange: nothing.
    Act: create a rectangle with no overrides.
    Assert: group_ids is an empty list by default.
    """
    element = build_rectangle()
    assert element.group_ids == []


def test_element_default_is_deleted_false():
    """
    Arrange: nothing.
    Act: create a rectangle with no overrides.
    Assert: is_deleted is False.
    """
    element = build_rectangle()
    assert element.is_deleted is False


def test_element_id_is_non_empty_string():
    """
    Arrange: nothing.
    Act: create a rectangle.
    Assert: the generated id is a non-empty string.
    """
    element = build_rectangle()
    assert isinstance(element.id, str)
    assert len(element.id) > 0


def test_element_ids_are_unique_per_instance():
    """
    Arrange: nothing.
    Act: create 50 rectangles.
    Assert: all IDs are distinct.
    """
    ids = {build_rectangle().id for _ in range(50)}
    assert len(ids) == 50


def test_build_rectangle_accepts_geometry_overrides():
    """
    Arrange: explicit x, y, width, height values.
    Act: create a rectangle with those overrides.
    Assert: the element carries the provided values.
    """
    element = build_rectangle(x=5.0, y=15.0, width=80.0, height=40.0)
    assert element.x == 5.0
    assert element.y == 15.0
    assert element.width == 80.0
    assert element.height == 40.0


def test_build_rectangle_accepts_style_overrides():
    """
    Arrange: explicit stroke_color and background_color.
    Act: create a rectangle with those overrides.
    Assert: the element carries the provided color strings.
    """
    element = build_rectangle(
        stroke_color="#ff0000", background_color="#00ff00"
    )
    assert element.stroke_color == "#ff0000"
    assert element.background_color == "#00ff00"


def test_to_dict_uses_camel_case_keys(rect):
    """
    Arrange: a rectangle element (from fixture).
    Act: call to_dict().
    Assert: camelCase keys are present (strokeColor, backgroundColor, groupIds, etc.).
    """
    result = rect.to_dict()
    assert "strokeColor" in result
    assert "backgroundColor" in result
    assert "groupIds" in result
    assert "strokeWidth" in result
    assert "strokeSharpness" in result
    assert "isDeleted" in result


def test_to_dict_snake_case_keys_absent(rect):
    """
    Arrange: a rectangle element (from fixture).
    Act: call to_dict().
    Assert: snake_case keys that were aliased are not in the output.
    """
    result = rect.to_dict()
    assert "stroke_color" not in result
    assert "background_color" not in result
    assert "group_ids" not in result


def test_to_dict_coordinates_rounded_to_two_decimal_places():
    """
    Arrange: an element with fractional coordinates beyond 2 decimal places.
    Act: call to_dict().
    Assert: x, y, width, height in the dict are rounded to 2 decimal places.
    """
    element = build_rectangle(x=1.2345, y=6.7891, width=99.9999, height=0.001)
    result = element.to_dict()
    assert result["x"] == pytest.approx(1.23)
    assert result["y"] == pytest.approx(6.79)
    assert result["width"] == pytest.approx(100.0)
    assert result["height"] == pytest.approx(0.0)


def test_to_dict_type_value_preserved(rect):
    """
    Arrange: a rectangle element.
    Act: call to_dict().
    Assert: 'type' key exists and equals 'rectangle'.
    """
    assert rect.to_dict()["type"] == "rectangle"


def test_linear_element_default_points_is_empty():
    """
    Arrange: nothing.
    Act: create a line with no overrides.
    Assert: points list is empty by default.
    """
    element = build_line()
    assert element.points == []


def test_linear_element_points_in_to_dict(line_element):
    """
    Arrange: a line element with two points (from fixture).
    Act: call to_dict().
    Assert: 'points' key is present in the result and contains the two points.
    """
    result = line_element.to_dict()
    assert "points" in result
    assert len(result["points"]) == 2


def test_linear_element_points_rounded_in_to_dict():
    """
    Arrange: a line with fractional point coordinates beyond 2 decimal places.
    Act: call to_dict().
    Assert: each coordinate within 'points' is rounded to 2 decimal places.
    """
    element = build_line(points=[[1.2345, 6.7891], [99.9999, 0.0001]])
    result = element.to_dict()
    assert result["points"][0] == [pytest.approx(1.23), pytest.approx(6.79)]
    assert result["points"][1] == [pytest.approx(100.0), pytest.approx(0.0)]


def test_linear_element_to_dict_includes_all_base_fields(line_element):
    """
    Arrange: a line element (from fixture).
    Act: call to_dict().
    Assert: all standard ExcalidrawElement fields are still present alongside 'points'.
    """
    result = line_element.to_dict()
    for key in (
        "type",
        "x",
        "y",
        "width",
        "height",
        "strokeColor",
        "opacity",
        "groupIds",
    ):
        assert key in result


def test_build_text_type_field():
    """
    Arrange: nothing.
    Act: create a text element via build_text().
    Assert: the 'type' field is 'text'.
    """
    element = build_text()
    assert element.type == "text"


def test_build_text_default_font_family():
    """
    Arrange: nothing.
    Act: create a text element with no overrides.
    Assert: font_family defaults to 1 (Virgil).
    """
    element = build_text()
    assert element.font_family == 1


def test_build_text_default_font_size():
    """
    Arrange: nothing.
    Act: create a text element with no overrides.
    Assert: font_size defaults to 20.
    """
    element = build_text()
    assert element.font_size == 20


def test_build_text_default_text_align():
    """
    Arrange: nothing.
    Act: create a text element with no overrides.
    Assert: text_align defaults to 'left'.
    """
    element = build_text()
    assert element.text_align == "left"


def test_build_text_stores_content():
    """
    Arrange: a text string.
    Act: create a text element with text and original_text set.
    Assert: both fields are stored correctly.
    """
    element = build_text(text="hello", original_text="hello")
    assert element.text == "hello"
    assert element.original_text == "hello"


def test_build_text_serializes_text_fields_to_camel_case():
    """
    Arrange: a text element with all key fields set.
    Act: call to_dict().
    Assert: text-specific fields appear in camelCase in the output.
    """
    element = build_text(
        text="hi",
        original_text="hi",
        font_family=2,
        font_size=16,
        text_align="center",
    )
    result = element.to_dict()
    assert result["text"] == "hi"
    assert result["originalText"] == "hi"
    assert result["fontFamily"] == 2
    assert result["fontSize"] == 16
    assert result["textAlign"] == "center"


def test_build_text_to_dict_includes_base_fields():
    """
    Arrange: a text element.
    Act: call to_dict().
    Assert: all standard ExcalidrawElement fields are present alongside text fields.
    """
    result = build_text(text="test", original_text="test").to_dict()
    for key in ("type", "x", "y", "width", "height", "strokeColor", "groupIds"):
        assert key in result
