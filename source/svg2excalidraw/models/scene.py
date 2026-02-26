import json

from .elements import ExcalidrawElement


class ExcalidrawScene:
    """Accumulates elements and serialises them to the Excalidraw JSON format."""

    def __init__(self) -> None:
        self.elements: list[ExcalidrawElement] = []

    def add(self, element: ExcalidrawElement) -> None:
        """
        Append an element to the scene.

        Parameters
        ----------
        element : ExcalidrawElement
            The element to add.
        """
        self.elements.append(element)

    def to_dict(self) -> dict:
        """
        Serialise the scene to an Excalidraw JSON-compatible dict.

        Returns
        -------
        dict
            Top-level Excalidraw document dict with ``type``, ``version``,
            ``source``, ``elements``, ``appState``, and ``files`` keys.
        """
        return {
            "type": "excalidraw",
            "version": 2,
            "source": "https://github.com/alanmmolina/svg2excalidraw",
            "elements": [element.to_dict() for element in self.elements],
            "appState": {"viewBackgroundColor": "#ffffff"},
            "files": {},
        }

    def to_json(self, indent: int = 2) -> str:
        """
        Serialise the scene to an indented JSON string.

        Parameters
        ----------
        indent : int, optional
            Number of spaces to use for indentation. Defaults to 2.

        Returns
        -------
        str
            JSON string representation of the scene.
        """
        return json.dumps(self.to_dict(), indent=indent)
