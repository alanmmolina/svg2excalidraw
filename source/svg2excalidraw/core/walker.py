import re
from collections.abc import Callable
from dataclasses import dataclass, field

from lxml import etree

from ..models.elements import (
    ExcalidrawElement,
    build_ellipse,
    build_line,
    build_rectangle,
)
from ..models.scene import ExcalidrawScene
from ..utils.geometry import bounding_dimensions, winding_order
from ..utils.identifiers import random_id
from .mapper import (
    accumulated_transform_matrix,
    transform_bounds,
    transform_points,
)
from .parser import parse
from .tracer import trace

_FLOAT_PATTERN: re.Pattern[str] = re.compile(
    r"\s*[+-]?(?:\d+\.?\d*|\.\d+)(?:[eE][+-]?\d+)?\s*"
)

_TAG_HANDLERS: dict[str, Callable[[etree._Element, "Context"], None]] = {}


@dataclass
class Context:
    """Mutable state threaded through the SVG tree walk."""

    root: etree._Element
    scene: ExcalidrawScene
    groups: list[etree._Element] = field(default_factory=list)
    group_id_cache: dict[int, str] = field(default_factory=dict)

    def group_ids(self) -> list[str]:
        """Stable Excalidraw group IDs for the current group stack."""
        return [self._stable_group_id(group) for group in self.groups]

    def _stable_group_id(self, group: etree._Element) -> str:
        key = id(group)
        if key not in self.group_id_cache:
            self.group_id_cache[key] = random_id()
        return self.group_id_cache[key]

    def push_group(self, element: etree._Element) -> "Context":
        """Return a new context with element appended to the group stack."""
        return Context(
            root=self.root,
            scene=self.scene,
            groups=[*self.groups, element],
            group_id_cache=self.group_id_cache,
        )


def _handles(tag: str) -> Callable:
    """Register a converter function as the handler for the given SVG tag name."""

    def register(fn: Callable) -> Callable:
        _TAG_HANDLERS[tag] = fn
        return fn

    return register


def _local_tag_name(element: etree._Element) -> str:
    """
    Get the local tag name of an element with any XML namespace prefix stripped.

    Parameters
    ----------
    element : etree._Element
        SVG element to inspect.

    Returns
    -------
    str
        Local tag name, e.g. ``"rect"`` for ``{http://www.w3.org/2000/svg}rect``,
        or an empty string if the tag is not a plain string.
    """
    match element.tag:
        case str() as tag if "}" in tag:
            return tag.split("}")[1]
        case str() as tag:
            return tag
        case _:
            return ""


def _float_attr(
    element: etree._Element, attribute_name: str, default: float = 0.0
) -> float:
    """
    Read a numeric XML attribute, returning a default if absent or non-numeric.

    Parameters
    ----------
    element : etree._Element
        SVG element to inspect.
    attribute_name : str
        Name of the XML attribute to read.
    default : float, optional
        Value to return when the attribute is absent or cannot be parsed. Defaults to 0.0.

    Returns
    -------
    float
        Parsed attribute value, or default.
    """
    value = element.get(attribute_name)
    if value is None or not _FLOAT_PATTERN.fullmatch(value):
        return default
    return float(value)


def _apply_presentation_attrs(
    element: etree._Element,
    excalidraw_element: ExcalidrawElement,
    context: Context,
) -> None:
    """
    Merge parsed SVG presentation attributes into an Excalidraw element in-place.

    Parameters
    ----------
    element : etree._Element
        The leaf SVG element.
    excalidraw_element : ExcalidrawElement
        The target Excalidraw element to update.
    context : Context
        Current walk context supplying the inherited group stack.
    """
    for field_name, field_value in parse(element, context.groups).items():
        if hasattr(excalidraw_element, field_name):
            setattr(excalidraw_element, field_name, field_value)


def _to_relative_points(
    absolute_points: list[tuple[float, float]],
) -> tuple[float, float, list[list[float]]]:
    """
    Convert a list of absolute points to an origin and origin-relative offsets.

    The first point in the list becomes the origin.

    Parameters
    ----------
    absolute_points : list[tuple[float, float]]
        Ordered sequence of (x, y) pairs in absolute coordinates.

    Returns
    -------
    tuple[float, float, list[list[float]]]
        A three-element tuple of (origin_x, origin_y, relative_points) where
        relative_points are offsets from the origin as ``[dx, dy]`` lists.
    """
    if not absolute_points:
        return 0.0, 0.0, []
    origin_x, origin_y = absolute_points[0]
    relative_points = [
        [point_x - origin_x, point_y - origin_y]
        for point_x, point_y in absolute_points
    ]
    return origin_x, origin_y, relative_points


def _parse_svg_points(points_str: str) -> list[tuple[float, float]]:
    """
    Parse the SVG ``points`` attribute of a polygon or polyline into coordinate pairs.

    Parameters
    ----------
    points_str : str
        Value of the ``points`` attribute, e.g. ``"0,0 10,5 20,0"``.

    Returns
    -------
    list[tuple[float, float]]
        Ordered sequence of (x, y) coordinate pairs.
    """
    tokens = points_str.replace(",", " ").split()
    return [
        (float(tokens[index]), float(tokens[index + 1]))
        for index in range(0, len(tokens) - 1, 2)
    ]


def _resolved_use_element(
    def_element: etree._Element, use_element: etree._Element
) -> etree._Element:
    """
    Return a copy of a ``<defs>`` element with overrideable attributes
    applied from a ``<use>`` element.

    Positional and sizing attributes (``x``, ``y``, ``width``, ``height``) are always
    taken from the ``<use>`` element; all other attributes fall back to the definition.

    Parameters
    ----------
    def_element : etree._Element
        The element referenced from ``<defs>``.
    use_element : etree._Element
        The ``<use>`` element referencing the definition.

    Returns
    -------
    etree._Element
        A deep copy of def_element with selected attributes overridden from use_element.
    """
    resolved = etree.fromstring(etree.tostring(def_element))
    always_override: frozenset[str] = frozenset(
        {"x", "y", "width", "height", "href", "xlink:href"}
    )
    for attribute_name, attribute_value in use_element.attrib.items():
        local_name = (
            attribute_name.split("}")[-1]
            if "}" in attribute_name
            else attribute_name
        )
        if local_name in always_override or not resolved.get(attribute_name):
            resolved.set(attribute_name, attribute_value)
    return resolved


@_handles("svg")
def _convert_svg(element: etree._Element, context: Context) -> None:
    """Walk all direct children of an ``<svg>`` element."""
    for child in element:
        walk(context, child)


@_handles("g")
def _convert_g(element: etree._Element, context: Context) -> None:
    """Push group context and walk all children of a ``<g>`` element."""
    child_context = context.push_group(element)
    for child in element:
        walk(child_context, child)


@_handles("use")
def _convert_use(element: etree._Element, context: Context) -> None:
    """Resolve a ``<use>`` element and walk the referenced definition."""
    href = element.get("href") or element.get(
        "{http://www.w3.org/1999/xlink}href"
    )
    if not href or not href.startswith("#"):
        return
    referenced = context.root.find(f'.//*[@id="{href[1:]}"]')
    if referenced is None:
        return
    walk(context, _resolved_use_element(referenced, element))


@_handles("rect")
def _convert_rect(element: etree._Element, context: Context) -> None:
    """Convert a ``<rect>`` element to an Excalidraw rectangle."""
    transform_matrix = accumulated_transform_matrix(element, context.groups)
    bounded_x, bounded_y, bounded_width, bounded_height = transform_bounds(
        _float_attr(element, "x"),
        _float_attr(element, "y"),
        _float_attr(element, "width"),
        _float_attr(element, "height"),
        transform_matrix,
    )
    is_round = element.get("rx") is not None or element.get("ry") is not None
    rect = build_rectangle(
        x=bounded_x,
        y=bounded_y,
        width=bounded_width,
        height=bounded_height,
        stroke_sharpness="round" if is_round else "sharp",
        group_ids=context.group_ids(),
    )
    _apply_presentation_attrs(element, rect, context)
    context.scene.add(rect)


@_handles("circle")
def _convert_circle(element: etree._Element, context: Context) -> None:
    """Convert a ``<circle>`` element to an Excalidraw ellipse."""
    radius = _float_attr(element, "r")
    center_x = _float_attr(element, "cx")
    center_y = _float_attr(element, "cy")
    transform_matrix = accumulated_transform_matrix(element, context.groups)
    bounded_x, bounded_y, bounded_width, bounded_height = transform_bounds(
        center_x - radius,
        center_y - radius,
        radius * 2,
        radius * 2,
        transform_matrix,
    )
    ellipse = build_ellipse(
        x=bounded_x,
        y=bounded_y,
        width=bounded_width,
        height=bounded_height,
        group_ids=context.group_ids(),
    )
    _apply_presentation_attrs(element, ellipse, context)
    context.scene.add(ellipse)


@_handles("ellipse")
def _convert_ellipse(element: etree._Element, context: Context) -> None:
    """Convert an ``<ellipse>`` element to an Excalidraw ellipse."""
    radius_x = _float_attr(element, "rx")
    radius_y = _float_attr(element, "ry")
    center_x = _float_attr(element, "cx")
    center_y = _float_attr(element, "cy")
    transform_matrix = accumulated_transform_matrix(element, context.groups)
    bounded_x, bounded_y, bounded_width, bounded_height = transform_bounds(
        center_x - radius_x,
        center_y - radius_y,
        radius_x * 2,
        radius_y * 2,
        transform_matrix,
    )
    ellipse = build_ellipse(
        x=bounded_x,
        y=bounded_y,
        width=bounded_width,
        height=bounded_height,
        group_ids=context.group_ids(),
    )
    _apply_presentation_attrs(element, ellipse, context)
    context.scene.add(ellipse)


@_handles("polygon")
def _convert_polygon(element: etree._Element, context: Context) -> None:
    """Convert a ``<polygon>`` element to a closed Excalidraw line."""
    raw_points = _parse_svg_points(element.get("points", ""))
    if not raw_points:
        return
    transform_matrix = accumulated_transform_matrix(element, context.groups)
    origin_x, origin_y, relative_points = _to_relative_points(
        transform_points(raw_points, transform_matrix)
    )
    relative_points.append([0.0, 0.0])
    width, height = bounding_dimensions(relative_points)
    line = build_line(
        x=origin_x,
        y=origin_y,
        width=width,
        height=height,
        points=relative_points,
        group_ids=context.group_ids(),
    )
    _apply_presentation_attrs(element, line, context)
    context.scene.add(line)


@_handles("polyline")
def _convert_polyline(element: etree._Element, context: Context) -> None:
    """Convert a ``<polyline>`` element to an Excalidraw line."""
    raw_points = _parse_svg_points(element.get("points", ""))
    if not raw_points:
        return
    transform_matrix = accumulated_transform_matrix(element, context.groups)
    origin_x, origin_y, relative_points = _to_relative_points(
        transform_points(raw_points, transform_matrix)
    )
    if element.get("fill", "none") not in ("none", "transparent", ""):
        relative_points.append([0.0, 0.0])
    width, height = bounding_dimensions(relative_points)
    line = build_line(
        x=origin_x,
        y=origin_y,
        width=width,
        height=height,
        points=relative_points,
        group_ids=context.group_ids(),
    )
    _apply_presentation_attrs(element, line, context)
    context.scene.add(line)


@_handles("line")
def _convert_line(element: etree._Element, context: Context) -> None:
    """Convert a ``<line>`` element to an Excalidraw line."""
    start_x = _float_attr(element, "x1")
    start_y = _float_attr(element, "y1")
    end_x = _float_attr(element, "x2")
    end_y = _float_attr(element, "y2")
    transform_matrix = accumulated_transform_matrix(element, context.groups)
    origin_x, origin_y, relative_points = _to_relative_points(
        transform_points([(start_x, start_y), (end_x, end_y)], transform_matrix)
    )
    width, height = bounding_dimensions(relative_points)
    line = build_line(
        x=origin_x,
        y=origin_y,
        width=width,
        height=height,
        points=relative_points,
        group_ids=context.group_ids(),
    )
    _apply_presentation_attrs(element, line, context)
    context.scene.add(line)


@_handles("path")
def _convert_path(element: etree._Element, context: Context) -> None:
    """Convert a ``<path>`` element to one Excalidraw line per sub-path, applying the fill rule."""
    path_data = element.get("d", "")
    if not path_data.strip():
        return

    transform_matrix = accumulated_transform_matrix(element, context.groups)
    fill_rule = element.get("fill-rule", "nonzero")
    subpaths = trace(path_data)
    path_group_id = random_id()
    fill_color = parse(element, context.groups).get(
        "background_color", "#000000"
    )
    initial_winding: str | None = None

    for subpath_index, raw_points in enumerate(subpaths):
        if not raw_points:
            continue

        absolute_points = transform_points(raw_points, transform_matrix)
        origin_x, origin_y, relative_points = _to_relative_points(
            absolute_points
        )
        width, height = bounding_dimensions(relative_points)

        if fill_rule == "nonzero":
            subpath_winding = winding_order(absolute_points)
            if subpath_index == 0:
                initial_winding = subpath_winding
            background_color = (
                fill_color if subpath_winding == initial_winding else "#ffffff"
            )
        else:
            background_color = (
                fill_color if subpath_index % 2 == 0 else "#ffffff"
            )

        line = build_line(
            x=origin_x,
            y=origin_y,
            width=width,
            height=height,
            points=relative_points,
            group_ids=[*context.group_ids(), path_group_id],
        )
        _apply_presentation_attrs(element, line, context)
        line.background_color = background_color
        context.scene.add(line)


def walk(context: Context, element: etree._Element) -> None:
    """Dispatch element to its tag handler, silently skipping unsupported tags."""
    if handler := _TAG_HANDLERS.get(_local_tag_name(element)):
        handler(element, context)
