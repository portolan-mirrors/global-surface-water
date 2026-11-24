#!/usr/bin/env python3
"""Build the global overview COG of one or more products from their tiles.

    python3 tools/make_overview.py catalog occurrence [change ...]
    python3 tools/make_overview.py --recolor catalog extent   # colour table only

Writes catalog/<product>/<product>-overview.tif: a mosaic of the tiles
resampled from 0.00025° to 0.004° (16x coarser), 180W to 180E and 80N to 60S
(90000 x 35000 px).

Each 40000 px tile is first resampled on its own to 2500 px (-ovr NONE, so
from the full-resolution pixels, not the tiles' own overviews), in parallel
across the cores. The small tiles are then mosaicked and written as one COG.
The method per product is in products.py: average for percentages, mode for
coded values, max for extent. Nodata 255 is set and the upstream colour table
is replaced by the default render colormap (tools/palette.py), so every
overview carries one. This is the only lossy file in the catalog, and it is for display.
"""
import os
import subprocess
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from products import NODATA, RESAMPLING  # noqa: E402
from palette import colormap  # noqa: E402

PX = 2500  # 40000 / 16
OVR = {"average": "AVERAGE", "mode": "MODE", "max": "MODE"}


def run(cmd):
    subprocess.run(cmd, check=True)


def set_palette(vrt, product):
    """Embed the default render colormap as the colour table, so QGIS and
    MapLibre (cog://) draw the overview in the Data Users Guide colours."""
    from osgeo import gdal
    gdal.UseExceptions()
    ds = gdal.Open(str(vrt), gdal.GA_Update)
    ct = gdal.ColorTable()
    for v, rgba in colormap(product).items():
        ct.SetColorEntry(int(v), tuple(rgba))
    b = ds.GetRasterBand(1)
    b.SetColorTable(ct)
    b.SetColorInterpretation(gdal.GCI_PaletteIndex)
    ds = None


def build(cat, product, tmp, pool):
    tiles = sorted((cat / product).glob("*/*.tif"))
    assert len(tiles) == 504, f"{product}: {len(tiles)} tiles"
    small = [tmp / f"{product}_{t.stem}.tif" for t in tiles]
    list(pool.map(run, [[
        "gdalwarp", "-q", "-overwrite", "-ovr", "NONE", "-ts", str(PX), str(PX),
        "-r", RESAMPLING[product], "-srcnodata", str(NODATA), "-dstnodata", str(NODATA),
        "-co", "COMPRESS=DEFLATE", str(t), str(s)] for t, s in zip(tiles, small)]))
    vrt = tmp / f"{product}.vrt"
    lst = tmp / f"{product}.txt"
    lst.write_text("\n".join(map(str, small)) + "\n")
    run(["gdalbuildvrt", "-q", "-te", "-180", "-60", "180", "80", "-vrtnodata", str(NODATA),
         "-input_file_list", str(lst), str(vrt)])
    set_palette(vrt, product)
    out = cat / product / f"{product}-overview.tif"
    run(["gdal_translate", "-q", "-of", "COG", "-a_nodata", str(NODATA),
         "-co", "COMPRESS=DEFLATE", "-co", "PREDICTOR=2", "-co", "LEVEL=6", "-co", "BLOCKSIZE=512",
         "-co", f"OVERVIEW_RESAMPLING={OVR[RESAMPLING[product]]}", "-co", "NUM_THREADS=8",
         "-co", "BIGTIFF=IF_SAFER", "-co", "SPARSE_OK=TRUE", str(vrt), str(out)])
    print(out, out.stat().st_size, flush=True)


def recolor(cat, product, tmp):
    """Rewrite an existing overview with the current colour table (no resampling)."""
    out = cat / product / f"{product}-overview.tif"
    vrt = tmp / f"{product}-recolor.vrt"
    run(["gdal_translate", "-q", "-of", "VRT", str(out), str(vrt)])
    set_palette(vrt, product)
    new = tmp / out.name
    run(["gdal_translate", "-q", "-of", "COG", "-co", "COMPRESS=DEFLATE", "-co", "PREDICTOR=2",
         "-co", "LEVEL=6", "-co", "BLOCKSIZE=512",
         "-co", f"OVERVIEW_RESAMPLING={OVR[RESAMPLING[product]]}", "-co", "NUM_THREADS=8",
         "-co", "BIGTIFF=IF_SAFER", "-co", "SPARSE_OK=TRUE", str(vrt), str(new)])
    os.replace(new, out)
    print("recoloured", out, out.stat().st_size, flush=True)


def main():
    if sys.argv[1] == "--recolor":
        cat = Path(sys.argv[2]).resolve()
        with tempfile.TemporaryDirectory(dir=cat.parent.parent / "work") as tmp:
            for product in sys.argv[3:]:
                recolor(cat, product, Path(tmp))
        return
    cat = Path(sys.argv[1]).resolve()
    work = cat.parent.parent / "work"
    work.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(dir=work) as tmp, \
            ThreadPoolExecutor(os.cpu_count()) as pool:
        for product in sys.argv[2:]:
            build(cat, product, Path(tmp), pool)


main()
