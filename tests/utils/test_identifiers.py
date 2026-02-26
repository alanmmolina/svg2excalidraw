import re

from source.svg2excalidraw.utils.identifiers import random_id, random_integer


def test_random_id_returns_string():
    """
    Arrange: nothing.
    Act: call random_id().
    Assert: result is a non-empty string.
    """
    result = random_id()
    assert isinstance(result, str)
    assert len(result) > 0


def test_random_id_uses_url_safe_characters():
    """
    Arrange: nothing.
    Act: generate 20 IDs.
    Assert: every ID contains only URL-safe characters (A-Z, a-z, 0-9, -, _).
    """
    for _ in range(20):
        result = random_id()
        assert re.fullmatch(r"[A-Za-z0-9_-]+", result), (
            f"ID contains unsafe chars: {result!r}"
        )


def test_random_id_minimum_length():
    """
    Arrange: nothing.
    Act: call random_id().
    Assert: length is at least 16 characters (secrets.token_urlsafe(16) produces ≥16).
    """
    result = random_id()
    assert len(result) >= 16


def test_random_id_uniqueness():
    """
    Arrange: nothing.
    Act: generate 200 IDs.
    Assert: all 200 are distinct (collision probability is negligible for a 16-byte token).
    """
    ids = {random_id() for _ in range(200)}
    assert len(ids) == 200


def test_random_integer_returns_int():
    """
    Arrange: nothing.
    Act: call random_integer().
    Assert: result is a Python int.
    """
    result = random_integer()
    assert isinstance(result, int)


def test_random_integer_lower_bound():
    """
    Arrange: nothing.
    Act: generate 50 integers.
    Assert: all values are non-negative (≥ 0).
    """
    assert all(random_integer() >= 0 for _ in range(50))


def test_random_integer_upper_bound():
    """
    Arrange: the maximum allowed value is 2**31 - 1.
    Act: generate 50 integers.
    Assert: all values are ≤ 2**31 - 1.
    """
    max_value = 2**31 - 1
    assert all(random_integer() <= max_value for _ in range(50))


def test_random_integers_are_varied():
    """
    Arrange: nothing.
    Act: generate 100 integers.
    Assert: at least 2 distinct values appear (i.e. not all the same constant).
    """
    values = {random_integer() for _ in range(100)}
    assert len(values) > 1
