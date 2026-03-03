from collections.abc import Callable
from typing import Any

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel

from ..utils.identifiers import random_id, random_integer


class ExcalidrawElement(BaseModel):
    """Geometry and visual style for a single Excalidraw shape."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    id: str = Field(default_factory=random_id)
    type: str
    x: float = 0.0
    y: float = 0.0
    width: float = 0.0
    height: float = 0.0
    angle: float = 0.0
    stroke_color: str = "#000000"
    background_color: str = "transparent"
    fill_style: str = "solid"
    stroke_width: float = 1.0
    stroke_style: str = "solid"
    stroke_sharpness: str = "sharp"
    roughness: int = 0
    opacity: int = 100
    seed: int = Field(default_factory=random_integer)
    version: int = 1
    version_nonce: int = Field(default_factory=random_integer)
    is_deleted: bool = False
    group_ids: list[str] = Field(default_factory=list)
    bound_element_ids: list[str] | None = None

    def to_dict(self) -> dict:
        """
        Serialise to a camelCase dict with coordinates rounded to 2 decimal places.

        Returns
        -------
        dict
            Excalidraw-compatible element dict with camelCase keys and
            ``x``, ``y``, ``width``, ``height`` rounded to 2 decimal places.
        """
        result = self.model_dump(by_alias=True)
        for coordinate_key in ("x", "y", "width", "height"):
            result[coordinate_key] = round(result[coordinate_key], 2)
        return result


class ExcalidrawLinearElement(ExcalidrawElement):
    """Excalidraw element with a variable-length point array (line, freedraw)."""

    points: list[list[float]] = Field(default_factory=list)

    def to_dict(self) -> dict:
        """
        Serialise to a camelCase dict with point coordinates rounded to 2 decimal places.

        Returns
        -------
        dict
            Excalidraw-compatible element dict with camelCase keys and all
            point coordinates rounded to 2 decimal places.
        """
        result = super().to_dict()
        result["points"] = [
            [round(coordinate_x, 2), round(coordinate_y, 2)]
            for coordinate_x, coordinate_y in self.points
        ]
        return result


class ExcalidrawTextElement(ExcalidrawElement):
    """Excalidraw text element."""

    type: str = "text"
    text: str = ""
    font_family: int = 1  # 1=Arial, 2=Virgil, 3=Cascadia
    font_size: float = 20
    baseline: float = 0.0
    text_align: str = "left"
    vertical_align: str = "top"
    original_text: str = ""

    def to_dict(self) -> dict:
        """
        Serialise to a camelCase dict with coordinates rounded to 2 decimal places.

        Returns
        -------
        dict
            Excalidraw-compatible element dict with camelCase keys and all
            coordinates rounded to 2 decimal places.
        """
        result = super().to_dict()
        return result


def _build_shape[T: ExcalidrawElement](
    model: type[T], element_type: str
) -> Callable[..., T]:
    """
    Return a factory that constructs ``model`` instances with a fixed ``type`` field.

    Parameters
    ----------
    model : type[T]
        The Pydantic model class to instantiate.
    element_type : str
        Value to assign to the ``type`` field of each constructed element.

    Returns
    -------
    Callable[..., T]
        A factory that accepts keyword overrides and returns a ``model`` instance
        with ``type`` fixed to ``element_type``.
    """

    def factory(**overrides: Any) -> T:
        return model(type=element_type, **overrides)

    return factory


build_rectangle = _build_shape(model=ExcalidrawElement, element_type="rectangle")
build_ellipse = _build_shape(model=ExcalidrawElement, element_type="ellipse")
build_line = _build_shape(model=ExcalidrawLinearElement, element_type="line")
build_text = _build_shape(model=ExcalidrawTextElement, element_type="text")
