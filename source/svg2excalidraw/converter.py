from lxml import etree

from .core.walker import Context, walk
from .models.scene import ExcalidrawScene


def convert(svg_string: str, *, as_json: bool = False) -> dict | str:
    """
    Convert an SVG string to an Excalidraw scene dict or JSON string.

    Parameters
    ----------
    svg_string : str
        Raw SVG markup to convert.
    as_json : bool, optional
        When ``True``, return a JSON string instead of a dict. Defaults to ``False``.

    Returns
    -------
    dict | str
        Excalidraw scene as a dict, or as an indented JSON string when ``as_json=True``.

    Raises
    ------
    ValueError
        If ``svg_string`` is not valid XML/SVG.
    """
    try:
        root = etree.fromstring(svg_string.encode(encoding="utf-8"))
    except etree.XMLSyntaxError as exc:
        raise ValueError(f"Invalid SVG: {exc}") from exc

    scene = ExcalidrawScene()
    walk(context=Context(root=root, scene=scene), element=root)
    return scene.to_json() if as_json else scene.to_dict()
