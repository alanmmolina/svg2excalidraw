from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from .converter import convert

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
    try:
        result = convert(body.svg)
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
