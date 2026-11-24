#!/usr/bin/env python3
"""Repair what `portolan readme` (portolan-cli 0.9.0) writes, after it runs.

- Root child links come out as `catalog/<id>/`; point them at `<id>/README.md`.
- The Files table lists every tile (504 rows). Collapse the tile rows into
  one row with the count and total size, generated from the table itself.
- The collection Quick Start opens a placeholder `image.tif` and reads the
  whole band (1.6 GB for one tile here). Replace it with a windowed read of
  a real tile at Tonle Sap.

    python3 -I tools/fix_readmes.py catalog
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from products import PUBLIC  # noqa: E402

root = Path(sys.argv[1]).resolve()
PLACEHOLDER = re.compile(r"```python\nimport rasterio\n\nwith rasterio.open\(\"image.tif\"\) as src:\n.*?```", re.S)


def quick_start(layer):
    return f'''```python
import rasterio
from rasterio.windows import from_bounds

# One 10° tile; rasterio fetches only the blocks inside the window.
url = "{PUBLIC}/{layer}/100E_20N/100E_20N.tif"
with rasterio.open(url) as src:
    win = from_bounds(103.6, 12.4, 104.6, 13.2, src.transform)  # Tonle Sap
    data = src.read(1, window=win)  # 255 is no data; the file sets no NoData tag
    print(data.shape, src.crs)
```'''


TILE_ROW = re.compile(r"^\| (\d+[EW]_\d+[NS])/\1\.tif \| ([\d.]+) (KB|MB|GB) \| [^|]* \|\n", re.M)
SOURCE_ROW = re.compile(r"^\| https://s3\.waw4-1\.cloudferro\.com/\S+ \| [^|]* \| [^|]* \|\n", re.M)
UNIT = {"KB": 1e-3, "MB": 1.0, "GB": 1e3}


def collapse_tiles(text):
    rows = TILE_ROW.findall(text)
    if len(rows) < 2:
        return text
    total_gb = sum(float(n) * UNIT[u] for _, n, u in rows) / 1e3
    first = TILE_ROW.search(text).start()
    text = TILE_ROW.sub("", text)
    n_src = len(SOURCE_ROW.findall(text))
    text = SOURCE_ROW.sub("", text)
    row = f"| `<tile>/<tile>.tif` ({len(rows)} tiles; see items.parquet) | {total_gb:.1f} GB total | - |\n"
    if n_src:
        row += f"| Upstream originals on CloudFerro ({n_src}, `source` assets) | same bytes | - |\n"
    return text[:first] + row + text[first:]


for readme in root.rglob("README.md"):
    rel = readme.parent.relative_to(root).as_posix()
    text = readme.read_text()
    if rel == ".":
        fixed = re.sub(r"\]\(catalog/([^)/]+)/\)", r"](\1/README.md)", text)
    else:
        fixed = collapse_tiles(PLACEHOLDER.sub(lambda m: quick_start(rel), text))
    if fixed != text:
        readme.write_text(fixed)
        print("fixed", readme.relative_to(root))
