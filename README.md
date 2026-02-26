# `svg2excalidraw`

Excalidraw has been a close friend for a long time. I use it to sketch architectural diagrams, mock up solutions, simulate scenarios, and pull ideas out of my head before they disappear. The best thing about it is how little it asks of you. You don't fight with the tool to make an arrow point the right way without it messing up everything else. You just draw and move on, and it looks good enough.

That "good enough" quality is intentional. Excalidraw encourages you to embrace the sloppiness of hand-drawn diagrams, and in engineering that's a genuine relief. Precision and rigor are already everywhere. Having a space that rewards loose thinking over polished output is worth protecting.

So I hadn't quite figured out what to do when I started wanting my diagrams to feel consistent even within that sloppiness, particularly in architectural sketches shared in professional contexts. Not polished, just coherent. The hand-drawn aesthetic, but with the same visual vocabulary across the board. 

> A bit contradictory, I know.

The existing [svg-to-excalidraw](https://github.com/excalidraw/svg-to-excalidraw/tree/main) package from the Excalidraw team was the closest thing to what I needed, but it hadn't seen a commit in 5 years. So I built my own version with a few additional parsers and a small web interface. You paste any SVG markup, whether it's a [Material Design](https://fonts.google.com/icons) icon, a [Feather](https://feathericons.com/) icon, or anything else you found on the web, and it hands you back the Excalidraw JSON you can paste directly into your canvas.


## How it works

The converter walks the SVG element tree and maps each supported tag to its Excalidraw equivalent. Presentation attributes like `fill`, `stroke`, and `opacity` are parsed and applied at the element level. Paths get broken into sub-paths, with `fill-rule` winding order deciding which sub-paths are holes and which are fills. Transforms accumulate as the walker descends through nested groups, so rotated or translated subtrees land at the right final coordinates. What comes out is a valid Excalidraw scene ready to paste into [Excalidraw](https://excalidraw.com).

## Web UI

The hosted version lives at [svg2excalidraw.alanmmolina.com](https://svg2excalidraw.alanmmolina.com). Paste your SVG markup, hit convert, and copy the resulting JSON straight into your Excalidraw canvas.

## Running locally

Clone the repo, sync dependencies with uv, and start the dev server:

```bash
git clone https://github.com/alanmmolina/svg2excalidraw
cd svg2excalidraw
uv sync
uv run task dev
```

The server starts at `http://localhost:8000`.

## Python API

If you'd rather skip the web interface and call the converter directly from Python, the `convert` function is the only thing you need:

```python
from svg2excalidraw.converter import convert

# Returns a dict
scene = convert(svg_string)

# Returns indented JSON
json_string = convert(svg_string, as_json=True)
```

## REST API

The server exposes two endpoints. Send your SVG as a JSON body to get back the Excalidraw scene:

**`POST /api/convert`**

```json
{ "svg": "<svg>...</svg>" }
```

Returns:

```json
{ "excalidraw": { "type": "excalidraw", "elements": [...], ... } }
```
