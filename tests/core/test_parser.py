import pytest
from lxml import etree

from source.svg2excalidraw.core.parser import (
    blend_alpha,
    parse,
    parse_color,
)


@pytest.fixture
def make_element():
    def _make(fragment: str) -> etree._Element:
        return etree.fromstring(fragment)

    return _make


def test_parse_color_six_digit_hex_passthrough():
    """
    Arrange: a valid 6-digit hex color string.
    Act: call parse_color.
    Assert: the same hex string is returned unchanged.
    """
    assert parse_color("#1a2b3c") == "#1a2b3c"


def test_parse_color_three_digit_hex_expands_to_six():
    """
    Arrange: a 3-digit CSS shorthand hex string '#fff'.
    Act: call parse_color.
    Assert: it expands to the full 6-digit form '#ffffff'.
    """
    assert parse_color("#fff") == "#ffffff"


def test_parse_color_three_digit_hex_black():
    """
    Arrange: the shorthand '#000'.
    Act: call parse_color.
    Assert: expands to '#000000'.
    """
    assert parse_color("#000") == "#000000"


def test_parse_color_three_digit_hex_mixed():
    """
    Arrange: the shorthand '#f0a'.
    Act: call parse_color.
    Assert: expands correctly to '#ff00aa'.
    """
    assert parse_color("#f0a") == "#ff00aa"


def test_parse_color_named_black():
    """
    Arrange: the CSS color name 'black'.
    Act: call parse_color.
    Assert: returns '#000000'.
    """
    assert parse_color("black") == "#000000"


def test_parse_color_named_white():
    """
    Arrange: the CSS color name 'white'.
    Act: call parse_color.
    Assert: returns '#ffffff'.
    """
    assert parse_color("white") == "#ffffff"


def test_parse_color_named_red():
    """
    Arrange: the CSS color name 'red'.
    Act: call parse_color.
    Assert: returns '#ff0000'.
    """
    assert parse_color("red") == "#ff0000"


def test_parse_color_case_insensitive_named_color():
    """
    Arrange: color names in mixed and upper case ('BLACK', 'Red').
    Act: call parse_color for each.
    Assert: both resolve correctly regardless of casing.
    """
    assert parse_color("BLACK") == "#000000"
    assert parse_color("Red") == "#ff0000"


def test_parse_color_none_returns_transparent():
    """
    Arrange: the SVG fill value 'none'.
    Act: call parse_color.
    Assert: returns 'transparent'.
    """
    assert parse_color("none") == "transparent"


def test_parse_color_transparent_returns_transparent():
    """
    Arrange: the CSS value 'transparent'.
    Act: call parse_color.
    Assert: returns 'transparent'.
    """
    assert parse_color("transparent") == "transparent"


def test_parse_color_rgb_function():
    """
    Arrange: an 'rgb(r, g, b)' CSS function string for red.
    Act: call parse_color.
    Assert: returns '#ff0000'.
    """
    assert parse_color("rgb(255, 0, 0)") == "#ff0000"


def test_parse_color_rgb_zero():
    """
    Arrange: 'rgb(0, 0, 0)'.
    Act: call parse_color.
    Assert: returns '#000000'.
    """
    assert parse_color("rgb(0, 0, 0)") == "#000000"


def test_parse_color_rgb_percentage_channels():
    """
    Arrange: 'rgb(100%, 0%, 0%)' — percentage form for pure red.
    Act: call parse_color.
    Assert: resolves to '#ff0000'.
    """
    assert parse_color("rgb(100%, 0%, 0%)") == "#ff0000"


def test_parse_color_rgba_opaque():
    """
    Arrange: 'rgba(255, 0, 0, 1)' — fully opaque red.
    Act: call parse_color.
    Assert: result starts with '#ff0000'.
    """
    result = parse_color("rgba(255, 0, 0, 1)")
    assert result.startswith("#ff0000")


def test_parse_color_rgba_fully_transparent():
    """
    Arrange: 'rgba(255, 0, 0, 0)' — fully transparent red.
    Act: call parse_color.
    Assert: result starts with '#ff0000' and ends with '00' (zero alpha).
    """
    result = parse_color("rgba(255, 0, 0, 0)")
    assert result.startswith("#ff0000")
    assert result.endswith("00")


def test_parse_color_unknown_string_returns_fallback():
    """
    Arrange: a completely unrecognized color string.
    Act: call parse_color.
    Assert: default fallback '#000000' is returned.
    """
    assert parse_color("notacolor") == "#000000"


def test_parse_color_empty_string_returns_fallback():
    """
    Arrange: an empty string.
    Act: call parse_color.
    Assert: default fallback '#000000' is returned.
    """
    assert parse_color("") == "#000000"


def test_parse_color_currentcolor_returns_fallback():
    """
    Arrange: the special SVG value 'currentColor' (cannot be resolved statically).
    Act: call parse_color.
    Assert: default fallback '#000000' is returned.
    """
    assert parse_color("currentColor") == "#000000"


def test_parse_color_custom_fallback():
    """
    Arrange: an unknown color and a custom fallback value '#ffffff'.
    Act: call parse_color with a custom fallback.
    Assert: the custom fallback is returned, not the default '#000000'.
    """
    assert parse_color("??", fallback="#ffffff") == "#ffffff"


def test_blend_alpha_full_opacity():
    """
    Arrange: a 6-digit red hex color and alpha 1.0.
    Act: call blend_alpha.
    Assert: result appends 'ff' alpha suffix → '#ff0000ff'.
    """
    assert blend_alpha("#ff0000", 1.0) == "#ff0000ff"


def test_blend_alpha_zero_opacity():
    """
    Arrange: a 6-digit red hex color and alpha 0.0.
    Act: call blend_alpha.
    Assert: result appends '00' alpha suffix → '#ff000000'.
    """
    assert blend_alpha("#ff0000", 0.0) == "#ff000000"


def test_blend_alpha_half_opacity():
    """
    Arrange: a red hex color and alpha 0.5.
    Act: call blend_alpha.
    Assert: round(0.5 * 255) = 128 = 0x80 → '#ff000080' (Python banker's rounding applies).
    """
    assert blend_alpha("#ff0000", 0.5) == "#ff000080"


def test_blend_alpha_transparent_passthrough():
    """
    Arrange: the special value 'transparent'.
    Act: call blend_alpha with any alpha.
    Assert: 'transparent' is returned unchanged (no hex channel to modify).
    """
    assert blend_alpha("transparent", 0.5) == "transparent"


def test_blend_alpha_none_passthrough():
    """
    Arrange: the SVG special value 'none'.
    Act: call blend_alpha.
    Assert: 'none' is returned unchanged.
    """
    assert blend_alpha("none", 0.5) == "none"


def test_blend_alpha_three_digit_hex_expands():
    """
    Arrange: the shorthand '#f00' and alpha 1.0.
    Act: call blend_alpha.
    Assert: shorthand is expanded internally and 'ff' alpha is appended → '#ff0000ff'.
    """
    assert blend_alpha("#f00", 1.0) == "#ff0000ff"


def test_blend_alpha_produces_nine_char_string():
    """
    Arrange: a 6-digit hex color and any alpha.
    Act: call blend_alpha.
    Assert: result is exactly 9 characters: '#' + 6 hex digits + 2 alpha digits.
    """
    result = blend_alpha("#123456", 0.75)
    assert len(result) == 9
    assert result.startswith("#")


def test_parse_attrs_stroke_color(make_element):
    """
    Arrange: an SVG rect element with stroke='#ff0000'.
    Act: call parse.
    Assert: 'stroke_color' in the result equals '#ff0000'.
    """
    element = make_element('<rect stroke="#ff0000"/>')
    result = parse(element, [])
    assert result["stroke_color"] == "#ff0000"


def test_parse_attrs_fill_none_gives_transparent(make_element):
    """
    Arrange: a rect with fill='none'.
    Act: call parse.
    Assert: 'background_color' is 'transparent'.
    """
    element = make_element('<rect fill="none"/>')
    result = parse(element, [])
    assert result["background_color"] == "transparent"


def test_parse_attrs_fill_color(make_element):
    """
    Arrange: a rect with fill='#00ff00'.
    Act: call parse.
    Assert: 'background_color' is '#00ff00'.
    """
    element = make_element('<rect fill="#00ff00"/>')
    result = parse(element, [])
    assert result["background_color"] == "#00ff00"


def test_parse_attrs_opacity_converted_to_100_scale(make_element):
    """
    Arrange: a rect with opacity='0.5'.
    Act: call parse.
    Assert: 'opacity' is 50 (multiplied by 100 for Excalidraw's 0-100 scale).
    """
    element = make_element('<rect opacity="0.5"/>')
    result = parse(element, [])
    assert result["opacity"] == 50


def test_parse_attrs_opacity_full(make_element):
    """
    Arrange: a rect with opacity='1'.
    Act: call parse.
    Assert: 'opacity' is 100.
    """
    element = make_element('<rect opacity="1"/>')
    assert parse(element, [])["opacity"] == 100


def test_parse_attrs_stroke_width(make_element):
    """
    Arrange: a rect with stroke-width='3'.
    Act: call parse.
    Assert: 'stroke_width' is 3.0.
    """
    element = make_element('<rect stroke-width="3"/>')
    result = parse(element, [])
    assert result["stroke_width"] == 3.0


def test_parse_attrs_inline_style_overrides_xml_attribute(make_element):
    """
    Arrange: a rect with both fill attribute and a conflicting fill in the style attribute.
    Act: call parse.
    Assert: the style attribute value wins (CSS specificity rule).
    """
    element = make_element('<rect fill="#0000ff" style="fill: #ff0000;"/>')
    result = parse(element, [])
    assert result["background_color"] == "#ff0000"


def test_parse_attrs_group_fill_inherited():
    """
    Arrange: a group element with fill='#aabbcc' and a plain child rect with no fill.
    Act: call parse on the child, passing the group.
    Assert: the child inherits 'background_color' from the group.
    """
    group = etree.fromstring('<g fill="#aabbcc"/>')
    child = etree.fromstring("<rect/>")
    result = parse(child, [group])
    assert result["background_color"] == "#aabbcc"


def test_parse_attrs_element_overrides_group():
    """
    Arrange: a group with fill='#aabbcc' and a child rect with its own fill='#112233'.
    Act: call parse on the child, passing the group.
    Assert: child's own fill wins over the inherited group value.
    """
    group = etree.fromstring('<g fill="#aabbcc"/>')
    child = etree.fromstring('<rect fill="#112233"/>')
    result = parse(child, [group])
    assert result["background_color"] == "#112233"


def test_parse_attrs_stroke_with_stroke_opacity(make_element):
    """
    Arrange: a rect with both stroke='#ff0000' and stroke-opacity='0.5'.
    Act: call parse.
    Assert: 'stroke_color' is present, starts with '#ff0000', and is 9 chars (with alpha).
    """
    element = make_element('<rect stroke="#ff0000" stroke-opacity="0.5"/>')
    result = parse(element, [])
    assert "stroke_color" in result
    assert result["stroke_color"].startswith("#ff0000")
    assert len(result["stroke_color"]) == 9


def test_parse_attrs_empty_element_returns_dict(make_element):
    """
    Arrange: a rect with no presentation attributes at all.
    Act: call parse.
    Assert: a dict is returned (may be empty or contain defaults; does not raise).
    """
    element = make_element("<rect/>")
    result = parse(element, [])
    assert isinstance(result, dict)


def test_parse_attrs_returns_dict_type(make_element):
    """
    Arrange: a basic rect element.
    Act: call parse.
    Assert: return type is dict.
    """
    element = make_element('<rect fill="red" stroke="blue"/>')
    result = parse(element, [])
    assert isinstance(result, dict)
