from svgelements import (
    Arc,
    Close,
    CubicBezier,
    Line,
    Move,
    Path,
    QuadraticBezier,
)

_COORDINATE_PRECISION = 4


def trace(
    path_data: str,
    curve_samples: int = 20,
) -> list[list[tuple[float, float]]]:
    """
    Trace an SVG path ``d`` attribute into sampled point lists, one list per sub-path.

    Closed sub-paths include the starting point as their final point.
    Curved segments (cubic/quadratic Bézier, arc) are approximated by sampling
    ``curve_samples`` evenly-spaced points along the curve.

    Parameters
    ----------
    path_data : str
        Value of an SVG ``d`` attribute, e.g. ``\"M 0 0 L 10 10 Z\"``.
    curve_samples : int, optional
        Number of points to sample per curved segment. Defaults to 20.

    Returns
    -------
    list[list[tuple[float, float]]]
        List of sub-paths, each being an ordered list of (x, y) coordinate pairs.
    """
    path = Path(path_data)

    subpaths: list[list[tuple[float, float]]] = []
    current_subpath: list[tuple[float, float]] = []
    move_point: tuple[float, float] | None = None

    for segment in path:
        match segment:
            case Move():
                if current_subpath:
                    subpaths.append(current_subpath)
                move_point = (
                    round(float(segment.end.x), _COORDINATE_PRECISION),
                    round(float(segment.end.y), _COORDINATE_PRECISION),
                )
                current_subpath = [move_point]

            case Close():
                if current_subpath and move_point is not None:
                    current_subpath.append(move_point)
                if current_subpath:
                    subpaths.append(current_subpath)
                current_subpath = []
                move_point = None

            case Line():
                current_subpath.append(
                    (
                        round(float(segment.end.x), _COORDINATE_PRECISION),
                        round(float(segment.end.y), _COORDINATE_PRECISION),
                    )
                )

            case CubicBezier() | QuadraticBezier() | Arc():
                for sample_index in range(1, curve_samples + 1):
                    sampled_point = segment.point(sample_index / curve_samples)
                    current_subpath.append(
                        (
                            round(
                                float(sampled_point.x), _COORDINATE_PRECISION
                            ),
                            round(
                                float(sampled_point.y), _COORDINATE_PRECISION
                            ),
                        )
                    )

    if current_subpath:
        subpaths.append(current_subpath)

    return subpaths
