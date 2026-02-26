import random as _random

from nanoid import generate as _nanoid_generate


def random_id() -> str:
    """
    Generate a unique nanoid-style identifier for an Excalidraw element.

    Returns
    -------
    str
        A random URL-safe string suitable for use as an element ID.
    """
    return _nanoid_generate()


def random_integer() -> int:
    """
    Generate a random 31-bit integer for use as a Rough.js render seed.

    Returns
    -------
    int
        A random integer in the range [0, 2^31 - 1].
    """
    return _random.randint(0, 2**31 - 1)
