import pytest
from lxml import etree

from source.svg2excalidraw.core.walker import Context, walk
from source.svg2excalidraw.models.scene import ExcalidrawScene


@pytest.fixture
def fresh_scene():
    return ExcalidrawScene()


@pytest.fixture
def svg_root():
    """A minimal SVG root element."""
    return etree.fromstring('<svg xmlns="http://www.w3.org/2000/svg"/>')


def test_walk_context_group_ids_empty_by_default(fresh_scene, svg_root):
    """
    Arrange: a Context with no groups on the stack.
    Act: call ctx.group_ids().
    Assert: the returned list is empty.
    """
    ctx = Context(root=svg_root, scene=fresh_scene)
    assert ctx.group_ids() == []


def test_walk_context_push_group_extends_stack(fresh_scene, svg_root):
    """
    Arrange: a Context and a group element.
    Act: call ctx.push_group(group_element).
    Assert: the new context has one item in its group stack; the original is unchanged.
    """
    ctx = Context(root=svg_root, scene=fresh_scene)
    group = etree.fromstring("<g/>")
    new_ctx = ctx.push_group(group)
    assert len(new_ctx.groups) == 1
    assert len(ctx.groups) == 0


def test_walk_context_push_group_does_not_mutate_original(
    fresh_scene, svg_root
):
    """
    Arrange: a Context with no groups.
    Act: call push_group.
    Assert: the original context's groups list is still empty.
    """
    ctx = Context(root=svg_root, scene=fresh_scene)
    ctx.push_group(etree.fromstring("<g/>"))
    assert ctx.groups == []


def test_walk_context_stable_group_id_same_element(fresh_scene, svg_root):
    """
    Arrange: a Context and a single group element.
    Act: call ctx.group_ids() twice on a context that contains the same group.
    Assert: both calls return the same ID string for that group.
    """
    group = etree.fromstring("<g/>")
    ctx = Context(root=svg_root, scene=fresh_scene).push_group(group)
    ids_first = ctx.group_ids()
    ids_second = ctx.group_ids()
    assert ids_first == ids_second


def test_walk_context_different_elements_get_different_ids(
    fresh_scene, svg_root
):
    """
    Arrange: two distinct group elements (different Python objects).
    Act: push each into its own context and get group IDs.
    Assert: the two groups receive different IDs.
    """
    group_a = etree.fromstring('<g id="a"/>')
    group_b = etree.fromstring('<g id="b"/>')
    ctx_a = Context(root=svg_root, scene=fresh_scene).push_group(group_a)
    ctx_b = Context(root=svg_root, scene=fresh_scene).push_group(group_b)
    assert ctx_a.group_ids() != ctx_b.group_ids()


def test_walk_context_shared_cache_preserves_ids_across_siblings(
    fresh_scene, svg_root
):
    """
    Arrange: one Context; two sibling elements pushed from the same parent group.
    Act: push the same group into a new context twice (same parent scenario).
    Assert: the same group element always yields the same ID, even across different ctx.
    """
    group = etree.fromstring("<g/>")
    ctx = Context(root=svg_root, scene=fresh_scene)
    child_ctx_1 = ctx.push_group(group)
    child_ctx_2 = ctx.push_group(group)
    assert child_ctx_1.group_ids() == child_ctx_2.group_ids()


def test_walk_rect_adds_one_element_to_scene(fresh_scene, svg_root):
    """
    Arrange: a rect element and a Context.
    Act: call walk() with the rect.
    Assert: one element is added to the scene.
    """
    ctx = Context(root=svg_root, scene=fresh_scene)
    rect = etree.fromstring('<rect x="0" y="0" width="10" height="10"/>')
    walk(ctx, rect)
    assert len(fresh_scene.elements) == 1


def test_walk_rect_adds_rectangle_type(fresh_scene, svg_root):
    """
    Arrange: a rect SVG element.
    Act: call walk() and inspect the scene.
    Assert: the added element has type 'rectangle'.
    """
    ctx = Context(root=svg_root, scene=fresh_scene)
    rect = etree.fromstring('<rect x="0" y="0" width="10" height="10"/>')
    walk(ctx, rect)
    assert fresh_scene.elements[0].type == "rectangle"


def test_walk_circle_adds_ellipse_type(fresh_scene, svg_root):
    """
    Arrange: a circle SVG element (SVG circles become Excalidraw ellipses).
    Act: call walk() and inspect the scene.
    Assert: the added element has type 'ellipse'.
    """
    ctx = Context(root=svg_root, scene=fresh_scene)
    circle = etree.fromstring('<circle cx="50" cy="50" r="30"/>')
    walk(ctx, circle)
    assert fresh_scene.elements[0].type == "ellipse"


def test_walk_line_adds_line_type(fresh_scene, svg_root):
    """
    Arrange: a line SVG element.
    Act: call walk() and inspect the scene.
    Assert: the added element has type 'line'.
    """
    ctx = Context(root=svg_root, scene=fresh_scene)
    line = etree.fromstring('<line x1="0" y1="0" x2="100" y2="0"/>')
    walk(ctx, line)
    assert fresh_scene.elements[0].type == "line"


def test_walk_unknown_tag_adds_nothing(fresh_scene, svg_root):
    """
    Arrange: an SVG element with a tag name not handled by the walker (e.g. <text>).
    Act: call walk() on it.
    Assert: no element is added to the scene and no exception is raised.
    """
    ctx = Context(root=svg_root, scene=fresh_scene)
    text_element = etree.fromstring("<text>hello</text>")
    walk(ctx, text_element)
    assert len(fresh_scene.elements) == 0


def test_walk_group_propagates_to_children(fresh_scene):
    """
    Arrange: an SVG with a group containing a rect.
    Act: call walk() on the group element (with the SVG root as context root).
    Assert: the child rect is added to the scene.
    """
    svg = etree.fromstring(
        '<svg xmlns="http://www.w3.org/2000/svg"><g><rect x="0" y="0" width="10" height="10"/></g></svg>'
    )
    ctx = Context(root=svg, scene=fresh_scene)
    walk(ctx, svg)
    assert len(fresh_scene.elements) == 1
    assert fresh_scene.elements[0].type == "rectangle"


def test_walk_group_assigns_shared_group_id_to_children(fresh_scene):
    """
    Arrange: an SVG group containing two child elements (rect + circle).
    Act: call walk() on the SVG root and collect the group IDs of both elements.
    Assert: both elements share the same non-empty group ID.
    """
    svg = etree.fromstring(
        '<svg xmlns="http://www.w3.org/2000/svg">'
        "<g>"
        '<rect x="0" y="0" width="5" height="5"/>'
        '<circle cx="10" cy="10" r="5"/>'
        "</g>"
        "</svg>"
    )
    ctx = Context(root=svg, scene=fresh_scene)
    walk(ctx, svg)
    assert len(fresh_scene.elements) == 2
    ids_0 = fresh_scene.elements[0].group_ids
    ids_1 = fresh_scene.elements[1].group_ids
    assert ids_0 == ids_1
    assert len(ids_0) >= 1


def test_walk_namespaced_element_is_dispatched_correctly(fresh_scene):
    """
    Arrange: an SVG rect element with the 'http://www.w3.org/2000/svg' namespace prefix.
    Act: call walk().
    Assert: the namespace prefix is stripped and the rect is handled correctly.
    """
    svg = etree.fromstring(
        '<svg xmlns="http://www.w3.org/2000/svg"><rect x="0" y="0" width="20" height="20"/></svg>'
    )
    rect = next(iter(svg))
    ctx = Context(root=svg, scene=fresh_scene)
    walk(ctx, rect)
    assert len(fresh_scene.elements) == 1
