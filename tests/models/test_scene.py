import json

import pytest

from source.svg2excalidraw.models.elements import (
    build_ellipse,
    build_line,
    build_rectangle,
)
from source.svg2excalidraw.models.scene import ExcalidrawScene


@pytest.fixture
def empty_scene():
    return ExcalidrawScene()


@pytest.fixture
def scene_with_rect():
    scene = ExcalidrawScene()
    scene.add(build_rectangle(x=0.0, y=0.0, width=50.0, height=25.0))
    return scene


def test_empty_scene_elements_list_is_empty(empty_scene):
    """
    Arrange: a freshly created ExcalidrawScene.
    Act: inspect the .elements attribute directly.
    Assert: it is an empty list.
    """
    assert empty_scene.elements == []


def test_empty_scene_to_dict_has_required_keys(empty_scene):
    """
    Arrange: a freshly created ExcalidrawScene.
    Act: call to_dict().
    Assert: keys 'type', 'version', 'source', 'elements', 'appState', 'files' are all present.
    """
    result = empty_scene.to_dict()
    for key in ("type", "version", "source", "elements", "appState", "files"):
        assert key in result


def test_scene_type_is_excalidraw(empty_scene):
    """
    Arrange: a freshly created ExcalidrawScene.
    Act: call to_dict() and check the 'type' field.
    Assert: value equals 'excalidraw'.
    """
    assert empty_scene.to_dict()["type"] == "excalidraw"


def test_scene_version_is_2(empty_scene):
    """
    Arrange: a freshly created ExcalidrawScene.
    Act: call to_dict() and read 'version'.
    Assert: value equals 2 (integer).
    """
    assert empty_scene.to_dict()["version"] == 2


def test_scene_elements_is_empty_list_in_dict(empty_scene):
    """
    Arrange: a freshly created ExcalidrawScene with no elements added.
    Act: call to_dict().
    Assert: 'elements' key maps to an empty list.
    """
    assert empty_scene.to_dict()["elements"] == []


def test_scene_files_is_empty_dict(empty_scene):
    """
    Arrange: a freshly created ExcalidrawScene.
    Act: call to_dict().
    Assert: 'files' key maps to an empty dict.
    """
    assert empty_scene.to_dict()["files"] == {}


def test_scene_app_state_has_background_color(empty_scene):
    """
    Arrange: a freshly created ExcalidrawScene.
    Act: call to_dict() and read 'appState'.
    Assert: 'viewBackgroundColor' key is present in appState.
    """
    assert "viewBackgroundColor" in empty_scene.to_dict()["appState"]


def test_add_single_element_appears_in_elements_list(scene_with_rect):
    """
    Arrange: a scene with one rectangle already added (from fixture).
    Act: call to_dict().
    Assert: 'elements' list contains exactly one item.
    """
    assert len(scene_with_rect.to_dict()["elements"]) == 1


def test_add_multiple_elements_all_appear_in_dict():
    """
    Arrange: three different elements (rect, ellipse, line).
    Act: add them to a scene and call to_dict().
    Assert: 'elements' list contains exactly three items.
    """
    scene = ExcalidrawScene()
    scene.add(build_rectangle())
    scene.add(build_ellipse())
    scene.add(build_line())
    assert len(scene.to_dict()["elements"]) == 3


def test_added_element_type_preserved_in_dict(scene_with_rect):
    """
    Arrange: a scene with a rectangle (from fixture).
    Act: call to_dict() and read the first element.
    Assert: element 'type' equals 'rectangle'.
    """
    element_dict = scene_with_rect.to_dict()["elements"][0]
    assert element_dict["type"] == "rectangle"


def test_added_element_uses_camel_case_keys(scene_with_rect):
    """
    Arrange: a scene with a rectangle (from fixture).
    Act: call to_dict() and inspect the first element.
    Assert: keys like 'strokeColor' and 'backgroundColor' are present (no snake_case).
    """
    element_dict = scene_with_rect.to_dict()["elements"][0]
    assert "strokeColor" in element_dict
    assert "backgroundColor" in element_dict
    assert "stroke_color" not in element_dict


def test_to_json_returns_string(empty_scene):
    """
    Arrange: a freshly created ExcalidrawScene.
    Act: call to_json().
    Assert: result is a string.
    """
    assert isinstance(empty_scene.to_json(), str)


def test_to_json_is_valid_json(empty_scene):
    """
    Arrange: a freshly created ExcalidrawScene.
    Act: call to_json() then json.loads() on the result.
    Assert: no exception is raised and parsed value is a dict.
    """
    result = json.loads(empty_scene.to_json())
    assert isinstance(result, dict)


def test_to_json_contains_type_field(empty_scene):
    """
    Arrange: a freshly created ExcalidrawScene.
    Act: parse to_json() output with json.loads.
    Assert: 'type' key is 'excalidraw'.
    """
    result = json.loads(empty_scene.to_json())
    assert result["type"] == "excalidraw"


def test_to_json_elements_match_to_dict(scene_with_rect):
    """
    Arrange: a scene with one rectangle (from fixture).
    Act: compare the 'elements' list from to_json() and to_dict().
    Assert: they are identical.
    """
    from_json = json.loads(scene_with_rect.to_json())["elements"]
    from_dict = scene_with_rect.to_dict()["elements"]
    assert from_json == from_dict
