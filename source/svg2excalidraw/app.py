import asyncio
from functools import partial
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from .converter import convert

MAX_SVG_BYTES = 512 * 1024  # 512 KB
MAX_PATH_ELEMENTS = 2_000
CONVERT_TIMEOUT_SECONDS = 30

app = FastAPI(title="svg2excalidraw", version="1.0.0")

_static_dir = Path(__file__).parent.parent.parent / "static"
_static_dir.mkdir(exist_ok=True)
app.mount(path="/static", app=StaticFiles(directory=_static_dir), name="static")


class ConvertRequest(BaseModel):
    """Request body for the /api/convert endpoint."""

    svg: str


class ConvertResponse(BaseModel):
    """Response body for the /api/convert endpoint."""

    excalidraw: dict


class ErrorResponse(BaseModel):
    """Error response body for the /api/convert endpoint."""

    error: str


@app.get(path="/", response_class=HTMLResponse)
async def index() -> HTMLResponse:
    """Serve the single-page UI."""
    html_path = _static_dir / "index.html"
    if html_path.exists():
        return HTMLResponse(content=html_path.read_text(encoding="utf-8"))
    return HTMLResponse(
        content="<h1>svg2excalidraw</h1><p>index.html not found.</p>"
    )


@app.post(path="/api/convert")
async def api_convert(body: ConvertRequest) -> JSONResponse:
    """Convert an SVG string to Excalidraw JSON."""
    if not body.svg.strip():
        return JSONResponse(
            content={"error": "SVG input is empty."}, status_code=400
        )

    svg_size = len(body.svg.encode("utf-8"))
    if svg_size > MAX_SVG_BYTES:
        return JSONResponse(
            content={
                "error": (
                    f"SVG too large ({svg_size // 1024}KB). "
                    f"Maximum allowed is {MAX_SVG_BYTES // 1024}KB."
                )
            },
            status_code=413,
        )

    path_count = body.svg.count("<path")
    if path_count > MAX_PATH_ELEMENTS:
        return JSONResponse(
            content={
                "error": (
                    f"SVG too complex ({path_count} path elements). "
                    f"Maximum allowed is {MAX_PATH_ELEMENTS}."
                )
            },
            status_code=413,
        )

    loop = asyncio.get_running_loop()
    try:
        result = await asyncio.wait_for(
            loop.run_in_executor(None, partial(convert, body.svg)),
            timeout=CONVERT_TIMEOUT_SECONDS,
        )
    except TimeoutError:
        return JSONResponse(
            content={
                "error": (
                    f"Conversion timed out after {CONVERT_TIMEOUT_SECONDS}s. "
                    "The SVG may be too complex to process."
                )
            },
            status_code=504,
        )
    except ValueError as exc:
        return JSONResponse(content={"error": str(exc)}, status_code=400)
    except Exception as exc:  # pragma: no cover
        return JSONResponse(
            content={"error": f"Conversion failed: {exc}"}, status_code=500
        )
    return JSONResponse(content={"excalidraw": result})


@app.get(path="/health")
async def health() -> dict:
    """Return service health status."""
    return {"status": "ok"}
