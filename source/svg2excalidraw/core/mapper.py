import math
import re

import numpy as np
from lxml.etree import _Element

_TRANSFORM_FUNCTION_PATTERN: re.Pattern[str] = re.compile(r"(\w+)\s*\(([^)]*)\)")
_NUMBER_PATTERN: re.Pattern[str] = re.compile(r"[-+]?(?:\d+\.?\d*|\.\d+)(?:[eE][-+]?\d+)?")


def _identity_matrix() -> np.ndarray:
    """
    Return a 3x3 identity matrix.

    Returns
    -------
    np.ndarray
        Shape (3, 3) float64 identity matrix.
    """
    return np.eye(3, dtype=float)


def _translation_matrix(translate_x: float, translate_y: float) -> np.ndarray:
    """
    Return a 3x3 affine matrix that translates by (translate_x, translate_y).

    Parameters
    ----------
    translate_x : float
        Horizontal translation distance.
    translate_y : float
        Vertical translation distance.

    Returns
    -------
    np.ndarray
        Shape (3, 3) affine translation matrix.
    """
    matrix = _identity_matrix()
    matrix[0, 2] = translate_x
    matrix[1, 2] = translate_y
    return matrix


def _scale_matrix(scale_x: float, scale_y: float) -> np.ndarray:
    """
    Return a 3x3 affine matrix that scales by (scale_x, scale_y).

    Parameters
    ----------
    scale_x : float
        Horizontal scale factor.
    scale_y : float
        Vertical scale factor.

    Returns
    -------
    np.ndarray
        Shape (3, 3) affine scale matrix.
    """
    matrix = _identity_matrix()
    matrix[0, 0] = scale_x
    matrix[1, 1] = scale_y
    return matrix


def _rotation_matrix(
    angle_radians: float, center_x: float = 0.0, center_y: float = 0.0
) -> np.ndarray:
    """
    Return a 3x3 affine matrix that rotates by angle_radians around (center_x, center_y).

    Parameters
    ----------
    angle_radians : float
        Rotation angle in radians, positive values rotate clockwise in SVG coordinates.
    center_x : float, optional
        X coordinate of the rotation center. Defaults to 0.0.
    center_y : float, optional
        Y coordinate of the rotation center. Defaults to 0.0.

    Returns
    -------
    np.ndarray
        Shape (3, 3) affine rotation matrix.
    """
    cos_angle = math.cos(angle_radians)
    sin_angle = math.sin(angle_radians)
    rotation = np.array(
        [
            [cos_angle, -sin_angle, 0.0],
            [sin_angle, cos_angle, 0.0],
            [0.0, 0.0, 1.0],
        ]
    )
    if center_x != 0.0 or center_y != 0.0:
        return (
            _translation_matrix(center_x, center_y)
            @ rotation
            @ _translation_matrix(-center_x, -center_y)
        )
    return rotation


def _skew_x_matrix(angle_degrees: float) -> np.ndarray:
    """
    Return a 3x3 affine matrix that skews along the X axis by angle_degrees.

    Parameters
    ----------
    angle_degrees : float
        Skew angle in degrees.

    Returns
    -------
    np.ndarray
        Shape (3, 3) affine skewX matrix.
    """
    matrix = _identity_matrix()
    matrix[0, 1] = math.tan(math.radians(angle_degrees))
    return matrix


def _skew_y_matrix(angle_degrees: float) -> np.ndarray:
    """
    Return a 3x3 affine matrix that skews along the Y axis by angle_degrees.

    Parameters
    ----------
    angle_degrees : float
        Skew angle in degrees.

    Returns
    -------
    np.ndarray
        Shape (3, 3) affine skewY matrix.
    """
    matrix = _identity_matrix()
    matrix[1, 0] = math.tan(math.radians(angle_degrees))
    return matrix


def _matrix_from_svg_args(
    scale_x: float,
    shear_y: float,
    shear_x: float,
    scale_y: float,
    translate_x: float,
    translate_y: float,
) -> np.ndarray:
    """
    Build a 3x3 matrix from SVG matrix(a,b,c,d,e,f) standard 2D affine args.

    Parameters
    ----------
    scale_x : float
        Horizontal scale component (a).
    shear_y : float
        Vertical shear component (b).
    shear_x : float
        Horizontal shear component (c).
    scale_y : float
        Vertical scale component (d).
    translate_x : float
        Horizontal translation component (e).
    translate_y : float
        Vertical translation component (f).

    Returns
    -------
    np.ndarray
        Shape (3, 3) affine matrix.
    """
    return np.array(
        [
            [scale_x, shear_x, translate_x],
            [shear_y, scale_y, translate_y],
            [0.0, 0.0, 1.0],
        ]
    )


def _extract_numbers(argument_string: str) -> list[float]:
    """
    Extract all numeric values from a transform function argument string.

    Parameters
    ----------
    argument_string : str
        Raw argument string from inside a transform function, e.g. ``"45 10,20"``.

    Returns
    -------
    list[float]
        Ordered list of parsed numeric values.
    """
    return [float(value) for value in _NUMBER_PATTERN.findall(argument_string)]


def _get_argument(arguments: list[float], index: int, default: float) -> float:
    """
    Return arguments[index] if it exists, otherwise default.

    Parameters
    ----------
    arguments : list[float]
        List of parsed numeric arguments.
    index : int
        Position to look up.
    default : float
        Fallback value when index is out of range.

    Returns
    -------
    float
        ``arguments[index]`` or ``default``.
    """
    return arguments[index] if len(arguments) > index else default


def _build_transform_matrix(function_name: str, numeric_arguments: list[float]) -> np.ndarray:
    """
    Build a 3x3 matrix for a single SVG transform function and its parsed arguments.

    Parameters
    ----------
    function_name : str
        Lowercase transform function name, e.g. ``"translate"`` or ``"rotate"``.
    numeric_arguments : list[float]
        Ordered numeric arguments extracted from the function call.

    Returns
    -------
    np.ndarray
        Shape (3, 3) affine matrix, or identity if the function name is unrecognised.
    """
    match function_name:
        case "matrix":
            return (
                _matrix_from_svg_args(*numeric_arguments[:6])
                if len(numeric_arguments) >= 6
                else _identity_matrix()
            )
        case "translate":
            return _translation_matrix(
                _get_argument(numeric_arguments, 0, 0.0),
                _get_argument(numeric_arguments, 1, 0.0),
            )
        case "scale":
            scale_x = _get_argument(numeric_arguments, 0, 1.0)
            return _scale_matrix(scale_x, _get_argument(numeric_arguments, 1, scale_x))
        case "rotate":
            return _rotation_matrix(
                math.radians(_get_argument(numeric_arguments, 0, 0.0)),
                _get_argument(numeric_arguments, 1, 0.0),
                _get_argument(numeric_arguments, 2, 0.0),
            )
        case "skewx":
            return _skew_x_matrix(_get_argument(numeric_arguments, 0, 0.0))
        case "skewy":
            return _skew_y_matrix(_get_argument(numeric_arguments, 0, 0.0))
        case _:
            return _identity_matrix()


def parse_transform_string(transform: str) -> np.ndarray:
    """
    Parse an SVG transform attribute into a single 3x3 affine matrix.

    Functions are composed left-to-right so the leftmost function is applied first.

    Parameters
    ----------
    transform : str
        Value of an SVG ``transform`` attribute, e.g. ``"translate(10,20) rotate(45)"``.

    Returns
    -------
    np.ndarray
        Shape (3, 3) accumulated affine matrix.
    """
    matrix = _identity_matrix()
    for transform_match in _TRANSFORM_FUNCTION_PATTERN.finditer(transform):
        matrix = matrix @ _build_transform_matrix(
            transform_match.group(1).lower(),
            _extract_numbers(transform_match.group(2)),
        )
    return matrix


def element_transform_matrix(element: "_Element") -> np.ndarray:
    """
    Return the transform matrix for a single SVG element.

    Parameters
    ----------
    element : _Element
        An lxml SVG element, optionally carrying a ``transform`` attribute.

    Returns
    -------
    np.ndarray
        Shape (3, 3) affine matrix, or identity if no ``transform`` attribute is present.
    """
    return (
        parse_transform_string(transform_attr)
        if (transform_attr := element.get("transform", ""))
        else _identity_matrix()
    )


def accumulated_transform_matrix(element: "_Element", groups: list["_Element"]) -> np.ndarray:
    """
    Return the accumulated transform through the group hierarchy and the element itself.

    Parameters
    ----------
    element : _Element
        The leaf SVG element whose final transform is being resolved.
    groups : list[_Element]
        Ancestor ``<g>`` elements ordered from outermost to innermost.

    Returns
    -------
    np.ndarray
        Shape (3, 3) affine matrix combining all ancestor group transforms
        and the element's own transform.
    """
    matrix = _identity_matrix()
    for group in groups:
        matrix = matrix @ element_transform_matrix(group)
    return matrix @ element_transform_matrix(element)


def transform_point(point_x: float, point_y: float, matrix: np.ndarray) -> tuple[float, float]:
    """
    Apply a 3x3 affine matrix to a single 2D point.

    Parameters
    ----------
    point_x : float
        X coordinate of the input point.
    point_y : float
        Y coordinate of the input point.
    matrix : np.ndarray
        Shape (3, 3) affine transformation matrix.

    Returns
    -------
    tuple[float, float]
        Transformed (x, y) coordinates.
    """
    transformed = matrix @ np.array([point_x, point_y, 1.0])
    return float(transformed[0]), float(transformed[1])


def transform_points(
    points: list[tuple[float, float]], matrix: np.ndarray
) -> list[tuple[float, float]]:
    """
    Apply a 3x3 affine matrix to every point in a list.

    Parameters
    ----------
    points : list[tuple[float, float]]
        Input (x, y) coordinates.
    matrix : np.ndarray
        Shape (3, 3) affine transformation matrix.

    Returns
    -------
    list[tuple[float, float]]
        Transformed coordinates in the same order as the input.
    """
    return [transform_point(point_x, point_y, matrix) for point_x, point_y in points]


def transform_bounds(
    origin_x: float,
    origin_y: float,
    width: float,
    height: float,
    matrix: np.ndarray,
) -> tuple[float, float, float, float]:
    """
    Transform axis-aligned bounds through a matrix, returning the new bounding box.

    All four corners of the rectangle are transformed and the axis-aligned
    bounding box of the results is returned.

    Parameters
    ----------
    origin_x : float
        X coordinate of the top-left corner.
    origin_y : float
        Y coordinate of the top-left corner.
    width : float
        Width of the input rectangle.
    height : float
        Height of the input rectangle.
    matrix : np.ndarray
        Shape (3, 3) affine transformation matrix.

    Returns
    -------
    tuple[float, float, float, float]
        ``(x, y, width, height)`` of the axis-aligned bounding box after transformation.
    """
    corners = [
        (origin_x, origin_y),
        (origin_x + width, origin_y),
        (origin_x, origin_y + height),
        (origin_x + width, origin_y + height),
    ]
    x_coords, y_coords = zip(*transform_points(corners, matrix), strict=False)
    min_x, min_y = min(x_coords), min(y_coords)
    return min_x, min_y, max(x_coords) - min_x, max(y_coords) - min_y
