---
name: Project Guidelines
description: This file describes the project guidelines for the SVG to Excalidraw converter.
applyTo: '**'
---

# Project Guidelines

## Architecture

SVG string → `converter.convert()` → lxml parse → `walker.walk()` → `ExcalidrawScene` → dict/JSON

| Layer | Files | Role |
|---|---|---|
| Entry | `converter.py` | Parses SVG with lxml, wires the pipeline, serializes output |
| Web | `app.py` | FastAPI layer; validates size/complexity limits, runs `convert()` in a thread executor with timeout |
| Walker | `core/walker.py` | Recursive tree traversal; dispatches by tag using `@_handles("tag")` registration |
| Parsing | `core/parser.py` | SVG presentation attribute extraction, CSS color resolution, group inheritance |
| Transforms | `core/mapper.py` | Accumulates affine transform matrices (numpy 3×3) down the group ancestry chain |
| Tracing | `core/tracer.py` | Samples `<path>` `d`-attributes into point lists via `svgelements`; uses `match`/`case` on segment types |
| Models | `models/elements.py` | Pydantic `BaseModel` subclasses with `alias_generator=to_camel`; factory via `_build_shape[T]` |
| Scene | `models/scene.py` | Plain (non-Pydantic) accumulator; `to_dict()` / `to_json()` produce the final Excalidraw document |
| Utils | `utils/geometry.py`, `utils/identifiers.py` | Bounding box math, winding order (shoelace), `random_id()` (nanoid), `random_integer()` (Rough.js seeds) |

## Adding a New SVG Element

Write a `@_handles("tagname")` function in `core/walker.py`. That is the only registration step required:

```python
@_handles("circle")
def _convert_circle(element: etree._Element, context: Context) -> None:
    ...
    context.scene.add(build_ellipse(...))
```

## Code Style

- Python 3.13; **no** `from __future__ import annotations`
- Unions as `X | Y`, optionals as `X | None`, generics via PEP 695 (`def fn[T: Base](...)`)
- LBYL everywhere: check conditions before acting, never use exceptions for control flow
- Exceptions caught only at boundaries: `converter.py` wraps `etree.XMLSyntaxError` → `ValueError`; `app.py` catches `ValueError` and `TimeoutError` at the HTTP boundary
- Variables declared close to use; inline single-use computations rather than extracting to intermediate locals
- No default parameter values unless the default is correct for ≥95% of callers

## Models

Pydantic `BaseModel` with `ConfigDict(alias_generator=to_camel, populate_by_name=True)`. Snake_case fields serialize to camelCase automatically via `model_dump(by_alias=True)`. Coordinate rounding is deferred to `to_dict()`, keeping internal floats precise throughout the pipeline.

## Build and Test

```bash
uv sync              # install all dependencies
uv run task dev      # start dev server at http://localhost:8000
uv run task test     # run full test suite (pytest -v)
uv run task fix      # auto-fix lint + format (ruff check --fix && ruff format)
uv run task check    # lint + format check without modifying files
```

## Test Conventions

- Module-level functions only — no test classes
- Every test docstring follows **Arrange / Act / Assert** structure
- Single assertion per test (or near-single)
- `conftest.py` provides `lxml_element` (parses SVG fragment) and `svg_wrap` (wraps body in `<svg>`) fixtures
- File-local helpers (e.g. `_svg()`, `_elements()`) are module-level functions, not fixtures

## Project Conventions

- `Context` is a `@dataclass`; `push_group()` returns a new instance (immutable stack) but shares `scene` and `group_id_cache` by reference — mutations on those objects propagate across all contexts
- Module-level constants in `app.py` (`MAX_SVG_BYTES`, `MAX_PATH_ELEMENTS`, `CONVERT_TIMEOUT_SECONDS`) are the abuse-prevention boundary — no middleware abstraction
- numpy `@` operator composes SVG transform matrices in `mapper.py`
- `match`/`case` used in `walker.py` (fallback dispatch) and `tracer.py` (path segment types)
