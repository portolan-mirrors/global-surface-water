"""Render one framed 3:2 PNG thumbnail per collection, and a contact sheet.

Each thumbnail frames one region at 1024 x 683 px in Web Mercator, over the
Esri World Light Gray canvas, coloured with the collection's default render
colormap (tools/stac.py: the Data Users Guide colours; "not water" and nodata
are transparent). Where the guide shows an example region for a layer, the
thumbnail uses it; transitions and extent use other regions so sibling cards
differ. Pixels come from the full-resolution tiles (via a VRT, so GDAL reads
the tiles' own overviews at this scale), with nearest-neighbour resampling.

    uv run -q --python /usr/bin/python3 --with pillow --with "numpy<2" \
        python -I tools/make_thumbs.py catalog work
"""
import math
import sys
from pathlib import Path

import numpy as np
from osgeo import gdal
from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).resolve().parent))
from palette import colormap  # noqa: E402

gdal.UseExceptions()
CAT, WORK = Path(sys.argv[1]).resolve(), Path(sys.argv[2]).resolve()
W, H = 1024, 683
R = 6378137.0
# (centre lon, centre lat, width in degrees of longitude, place)
FRAMES = {
    "occurrence": (104.6, 12.4, 3.6, "Tonle Sap and the Mekong, Cambodia"),  # guide: Mekong
    "change": (90.6, 25.6, 4.2, "Brahmaputra, Assam and Bangladesh"),        # guide: Brahmaputra
    "seasonality": (-4.4, 14.9, 2.6, "Inner Niger Delta near Mopti, Mali"),   # guide: Mopti
    "recurrence": (-90.7, 35.4, 2.2, "Mississippi floodplain, north-east Arkansas"),  # guide: NE Arkansas
    "transitions": (59.8, 45.0, 6.5, "Aral Sea, Kazakhstan and Uzbekistan"),
    "extent": (-60.2, -3.2, 4.0, "Amazon and Rio Negro near Manaus, Brazil"),
}
BASEMAP = """<GDAL_WMS><Service name="TMS"><ServerUrl>https://services.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Light_Gray_Base/MapServer/tile/${z}/${y}/${x}</ServerUrl></Service>
<DataWindow><UpperLeftX>-20037508.34</UpperLeftX><UpperLeftY>20037508.34</UpperLeftY><LowerRightX>20037508.34</LowerRightX><LowerRightY>-20037508.34</LowerRightY><TileLevel>15</TileLevel><TileCountX>1</TileCountX><TileCountY>1</TileCountY><YOrigin>top</YOrigin></DataWindow>
<Projection>EPSG:3857</Projection><BlockSizeX>256</BlockSizeX><BlockSizeY>256</BlockSizeY><BandsCount>3</BandsCount></GDAL_WMS>"""


def merc(lon, lat):
    return R * math.radians(lon), R * math.log(math.tan(math.pi / 4 + math.radians(lat) / 2))


def bounds(lon, lat, width):
    cx, cy = merc(lon, lat)
    half_w = R * math.radians(width) / 2
    half_h = half_w * H / W
    return [cx - half_w, cy - half_h, cx + half_w, cy + half_h]


def warp(src, b, alg, **kw):
    return gdal.Warp("", src, format="MEM", dstSRS="EPSG:3857", outputBounds=b, width=W, height=H,
                     resampleAlg=alg, **kw).ReadAsArray()


def lut(product):
    cm = colormap(product)
    t = np.zeros((256, 4), np.float32)
    for k, v in cm.items():
        t[int(k)] = v
    return t


def main():
    WORK.mkdir(exist_ok=True)
    out = {}
    for product, (lon, lat, width, place) in FRAMES.items():
        vrt = WORK / f"thumb-{product}.vrt"
        gdal.BuildVRT(str(vrt), [str(p) for p in sorted((CAT / product).glob("*/*.tif"))])
        b = bounds(lon, lat, width)
        try:
            base = warp(BASEMAP, b, "bilinear").transpose(1, 2, 0).astype(np.float32)
        except RuntimeError:
            base = np.full((H, W, 3), 235, np.float32)
        a = warp(str(vrt), b, "near")
        rgba = lut(product)[a]
        alpha = rgba[..., 3:4] / 255
        img = base * (1 - alpha) + rgba[..., :3] * alpha
        path = CAT / product / "thumbnail.png"
        Image.fromarray(img.astype(np.uint8)).save(path, optimize=True)
        cover = float((alpha[..., 0] > 0).mean())
        out[product] = (path, place, cover)
        print(f"{product:12s} {place:45s} coloured px {cover:6.1%} {path.stat().st_size} B")
    sheet = Image.new("RGB", (2 * W + 30, 3 * (H + 40) + 10), "white")
    d = ImageDraw.Draw(sheet)
    for i, (product, (path, place, cover)) in enumerate(out.items()):
        x, y = 10 + (i % 2) * (W + 10), 10 + (i // 2) * (H + 40)
        sheet.paste(Image.open(path), (x, y + 30))
        d.text((x, y + 8), f"{product}: {place} ({cover:.0%} coloured)", fill="black")
    sheet.save(WORK / "contact-sheet.png")


main()
