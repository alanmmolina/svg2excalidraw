from collections.abc import Sequence


def bounding_dimensions(points: list[Sequence[float]]) -> tuple[float, float]:
    """
    Compute the width and height of the axis-aligned bounding box for a point list.

    Parameters
    ----------
    points : list[Sequence[float]]
        Ordered sequence of points, each with at least two coordinates ``[x, y]``.

    Returns
    -------
    tuple[float, float]
        ``(width, height)`` of the bounding box, or ``(0.0, 0.0)`` for an empty list.
    """
    if not points:
        return 0.0, 0.0
    x_coords = [point[0] for point in points]
    y_coords = [point[1] for point in points]
    return max(x_coords) - min(x_coords), max(y_coords) - min(y_coords)


def winding_order(points: list[tuple[float, float]]) -> str:
    """
    Determine the winding order of a polygon using the shoelace formula.

    A positive shoelace sum indicates clockwise winding in SVG coordinates
    (where the Y axis increases downward).

    Parameters
    ----------
    points : list[tuple[float, float]]
        Ordered sequence of (x, y) vertices forming a closed polygon.

    Returns
    -------
    str
        ``"clockwise"`` or ``"counterclockwise"``.
    """
    total = sum(
        (points[(index + 1) % len(points)][0] - point[0])
        * (points[(index + 1) % len(points)][1] + point[1])
        for index, point in enumerate(points)
    )
    return "clockwise" if total > 0 else "counterclockwise"
