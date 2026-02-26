import re

from lxml.etree import _Element

_NAMED_COLORS: dict[str, str] = {
    "black": "#000000",
    "white": "#ffffff",
    "red": "#ff0000",
    "green": "#008000",
    "blue": "#0000ff",
    "yellow": "#ffff00",
    "orange": "#ffa500",
    "purple": "#800080",
    "pink": "#ffc0cb",
    "gray": "#808080",
    "grey": "#808080",
    "silver": "#c0c0c0",
    "navy": "#000080",
    "teal": "#008080",
    "aqua": "#00ffff",
    "cyan": "#00ffff",
    "fuchsia": "#ff00ff",
    "magenta": "#ff00ff",
    "maroon": "#800000",
    "olive": "#808000",
    "lime": "#00ff00",
    "brown": "#a52a2a",
    "indigo": "#4b0082",
    "violet": "#ee82ee",
    "coral": "#ff7f50",
    "salmon": "#fa8072",
    "gold": "#ffd700",
    "tan": "#d2b48c",
    "ivory": "#fffff0",
    "beige": "#f5f5dc",
    "lavender": "#e6e6fa",
    "khaki": "#f0e68c",
    "crimson": "#dc143c",
    "turquoise": "#40e0d0",
    "sienna": "#a0522d",
    "chocolate": "#d2691e",
    "tomato": "#ff6347",
    "steelblue": "#4682b4",
    "slategray": "#708090",
    "slategrey": "#708090",
    "darkgreen": "#006400",
    "darkblue": "#00008b",
    "darkred": "#8b0000",
    "darkgray": "#a9a9a9",
    "darkgrey": "#a9a9a9",
    "lightgray": "#d3d3d3",
    "lightgrey": "#d3d3d3",
    "lightblue": "#add8e6",
    "lightgreen": "#90ee90",
    "lightyellow": "#ffffe0",
    "lightpink": "#ffb6c1",
    "whitesmoke": "#f5f5f5",
    "snow": "#fffafa",
    "transparent": "transparent",
    "none": "transparent",
}

_PRESENTATION_ATTRIBUTES: frozenset[str] = frozenset(
    {
        "stroke",
        "stroke-opacity",
        "stroke-width",
        "fill",
        "fill-opacity",
        "fill-rule",
        "opacity",
    }
)


def _clamp(value: float, minimum: int, maximum: int) -> int:
    """
    Clamp value to [minimum, maximum] after rounding.

    Parameters
    ----------
    value : float
        The value to clamp.
    minimum : int
        Lower bound (inclusive).
    maximum : int
        Upper bound (inclusive).

    Returns
    -------
    int
        Rounded value clamped to [minimum, maximum].
    """
    return max(minimum, min(maximum, round(value)))


def _css_channel_to_byte(channel_str: str) -> int:
    """
    Convert a CSS color channel string (plain number or percentage) to a 0-255 byte.

    Parameters
    ----------
    channel_str : str
        Raw channel value, e.g. ``"128"`` or ``"50%"``.

    Returns
    -------
    int
        Integer channel value in the range [0, 255].
    """
    return (
        _clamp(float(channel_str[:-1]) * 2.55, 0, 255)
        if channel_str.endswith("%")
        else _clamp(float(channel_str), 0, 255)
    )


def parse_color(value: str, fallback: str = "#000000") -> str:
    """
    Resolve any SVG color string to a CSS hex string or 'transparent'.

    Parameters
    ----------
    value : str
        Raw SVG color value, e.g. ``"red"``, ``"#ff0000"``, ``"rgb(255,0,0)"``.
    fallback : str, optional
        Hex color to return when the value is empty or unrecognised. Defaults to ``"#000000"``.

    Returns
    -------
    str
        Lowercase 6- or 8-digit CSS hex string, or ``"transparent"``.
    """
    if not value:
        return fallback

    normalized = value.strip().lower()

    if normalized in ("none", "transparent"):
        return "transparent"

    if normalized in _NAMED_COLORS:
        return _NAMED_COLORS[normalized]

    if normalized == "currentcolor":
        return fallback

    if color_match := re.fullmatch(
        r"#([0-9a-f])([0-9a-f])([0-9a-f])", normalized
    ):
        return f"#{color_match.group(1) * 2}{color_match.group(2) * 2}{color_match.group(3) * 2}"

    if re.fullmatch(r"#[0-9a-f]{6}([0-9a-f]{2})?", normalized):
        return normalized

    if color_match := re.fullmatch(
        r"rgb\(\s*([0-9.]+%?)\s*,\s*([0-9.]+%?)\s*,\s*([0-9.]+%?)\s*\)",
        normalized,
    ):
        red = _css_channel_to_byte(color_match.group(1))
        green = _css_channel_to_byte(color_match.group(2))
        blue = _css_channel_to_byte(color_match.group(3))
        return f"#{red:02x}{green:02x}{blue:02x}"

    if color_match := re.fullmatch(
        r"rgba\(\s*([0-9.]+%?)\s*,\s*([0-9.]+%?)\s*,\s*([0-9.]+%?)\s*,\s*([0-9.]+)\s*\)",
        normalized,
    ):
        red = _css_channel_to_byte(color_match.group(1))
        green = _css_channel_to_byte(color_match.group(2))
        blue = _css_channel_to_byte(color_match.group(3))
        alpha_byte = _clamp(float(color_match.group(4)) * 255, 0, 255)
        return f"#{red:02x}{green:02x}{blue:02x}{alpha_byte:02x}"

    return fallback


def blend_alpha(hex_color: str, alpha: float) -> str:
    """
    Set the alpha channel of a hex color to the given 0.0-1.0 value.

    Parameters
    ----------
    hex_color : str
        3-, 6-, or 8-digit CSS hex color string, or ``"transparent"`` / ``"none"``.
    alpha : float
        Opacity in the range [0.0, 1.0].

    Returns
    -------
    str
        8-digit hex color string with the alpha channel applied,
        or the original string unchanged if it is transparent or invalid.
    """
    if hex_color in ("transparent", "none"):
        return hex_color

    hex_string = hex_color.lstrip("#")
    if len(hex_string) == 3:
        hex_string = "".join(digit * 2 for digit in hex_string)
    if len(hex_string) not in (6, 8):
        return hex_color

    red = int(hex_string[0:2], 16)
    green = int(hex_string[2:4], 16)
    blue = int(hex_string[4:6], 16)
    alpha_byte = _clamp(alpha * 255, 0, 255)
    return f"#{red:02x}{green:02x}{blue:02x}{alpha_byte:02x}"


def _parse_inline_style(style: str) -> dict[str, str]:
    """
    Parse a CSS inline style string into a property→value mapping.

    Parameters
    ----------
    style : str
        Value of an SVG ``style`` attribute, e.g. ``"fill: red; stroke: none"``.

    Returns
    -------
    dict[str, str]
        Mapping of lowercased property names to their trimmed values.
    """
    return {
        property_name.strip().lower(): property_value.strip()
        for declaration in style.split(";")
        if ":" in declaration
        for property_name, _, property_value in [declaration.partition(":")]
    }


def _element_attr(element: _Element, name: str) -> str | None:
    """
    Get an attribute value, checking both the plain name and any XML namespace prefix.

    Parameters
    ----------
    element : _Element
        The lxml SVG element to inspect.
    name : str
        Local attribute name to look up, e.g. ``"stroke-width"``.

    Returns
    -------
    str | None
        Attribute value if found, otherwise ``None``.
    """
    if (value := element.get(name)) is not None:
        return value
    return next(
        (
            attribute_value
            for attribute_key, attribute_value in element.attrib.items()
            if attribute_key.split("}")[-1] == name
        ),
        None,
    )


def _extract_presentation_attrs(element: _Element) -> dict[str, str]:
    """
    Collect presentation attributes from a single element, with inline style taking priority.

    Parameters
    ----------
    element : _Element
        The lxml SVG element to inspect.

    Returns
    -------
    dict[str, str]
        Mapping of presentation attribute names to their string values.
        Inline ``style`` declarations override XML attribute values.
    """
    result = {
        attribute_name: value
        for attribute_name in _PRESENTATION_ATTRIBUTES
        if (value := _element_attr(element, attribute_name)) is not None
    }
    if style := _element_attr(element, "style"):
        result.update(_parse_inline_style(style))
    return result


def _map_to_excalidraw_fields(attributes: dict[str, str]) -> dict:
    """
    Convert raw SVG attribute dict to Excalidraw element field values.

    Parameters
    ----------
    attributes : dict[str, str]
        Merged presentation attributes from group ancestors and the leaf element.

    Returns
    -------
    dict
        Partial Excalidraw element field mapping with keys such as
        ``stroke_color``, ``background_color``, ``opacity``, and ``stroke_width``.
    """
    result: dict = {}

    if stroke := attributes.get("stroke"):
        color = parse_color(stroke, "#000000")
        result["stroke_color"] = (
            blend_alpha(color, float(attributes["stroke-opacity"]))
            if "stroke-opacity" in attributes and color != "transparent"
            else color
        )
    elif stroke_opacity := attributes.get("stroke-opacity"):
        result["stroke_color"] = blend_alpha("#000000", float(stroke_opacity))

    if fill := attributes.get("fill"):
        color = parse_color(fill, "transparent")
        result["background_color"] = (
            blend_alpha(color, float(attributes["fill-opacity"]))
            if "fill-opacity" in attributes and color != "transparent"
            else color
        )
    elif fill_opacity := attributes.get("fill-opacity"):
        result["background_color"] = blend_alpha("#000000", float(fill_opacity))

    if opacity := attributes.get("opacity"):
        result["opacity"] = round(float(opacity) * 100)

    if stroke_width := attributes.get("stroke-width"):
        result["stroke_width"] = float(stroke_width)

    return result


def parse(element: _Element, groups: list[_Element]) -> dict:
    """
    Merge SVG presentation attributes from group ancestors and the element into Excalidraw fields.

    Parameters
    ----------
    element : _Element
        The leaf SVG element to parse.
    groups : list[_Element]
        Ancestor ``<g>`` elements ordered from outermost to innermost.

    Returns
    -------
    dict
        Excalidraw element field mapping produced by accumulating presentation
        attributes from the outermost group down to the element itself,
        with later values taking priority.
    """
    return _map_to_excalidraw_fields(
        {
            key: value
            for node in [*groups, element]
            for key, value in _extract_presentation_attrs(node).items()
        }
    )
