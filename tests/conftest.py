import pytest
from lxml import etree


@pytest.fixture
def lxml_element():
    """Factory fixture: creates an lxml element from an SVG fragment string."""

    def _make(fragment: str) -> etree._Element:
        return etree.fromstring(fragment)

    return _make


@pytest.fixture
def svg_wrap():
    """Factory fixture: wraps SVG body in a root <svg> element."""

    def _wrap(inner: str, view_box: str = "0 0 200 200") -> str:
        return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{view_box}">{inner}</svg>'

    return _wrap
