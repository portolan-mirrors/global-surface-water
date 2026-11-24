#!/usr/bin/env python3
"""Write the STAC JSON and collection metadata.yaml files for the catalog.

    python3 -I tools/stac.py catalog manifest/upstream.json

Writes everything from tools/products.py, the root .portolan/metadata.yaml,
and the upstream manifest; it reads no pixels. It is idempotent. The tile
bytes are not hashed: file:checksum is a SHOULD, and every tile was checked
against the upstream hash when it was downloaded (tools/build.sh).

Per collection:
  .portolan/metadata.yaml  title, description, processing notes
  collection.json          extent, providers, item_assets, renders, assets
                           (overview COG, thumbnail), via/license/docs links
  <tile>/<tile>.json       one item per 10° tile: data asset (the copied COG)
                           and source asset (the upstream object)
Root catalog.json: child, self, vcs, issues, icon links.
"""
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
from palette import colormap  # noqa: E402
from products import (DOWNLOAD_PAGE, GUIDE, NODATA, PRODUCTS, PUBLIC, REPO,  # noqa: E402
                      RESAMPLING, UPSTREAM)

COG = "image/tiff; application=geotiff; profile=cloud-optimized"
PORTOLAN = "https://schemas.portolan-sdi.org/portolan/v0.2.0/schema.json"
EXT = {
    "file": "https://stac-extensions.github.io/file/v2.1.0/schema.json",
    "proj": "https://stac-extensions.github.io/projection/v2.0.0/schema.json",
    "raster": "https://stac-extensions.github.io/raster/v2.0.0/schema.json",
    "render": "https://stac-extensions.github.io/render/v2.0.0/schema.json",
    "classification": "https://stac-extensions.github.io/classification/v2.0.0/schema.json",
    "item_assets": "https://stac-extensions.github.io/item-assets/v1.0.0/schema.json",
}
RES = 0.00025
TILE = re.compile(r"^(\d+)([EW])_(\d+)([NS])$")
def load(p):
    return json.loads(Path(p).read_text())


def save(p, d):
    Path(p).write_text(json.dumps(d, indent=2, ensure_ascii=False) + "\n")


def tile_bbox(t):
    m = TILE.match(t)
    lon = int(m[1]) * (1 if m[2] == "E" else -1)
    lat = int(m[3]) * (1 if m[4] == "N" else -1)
    return [lon, lat - 10, lon + 10, lat]  # the name is the upper-left corner


def _cls(v, c, lbl):
    d = {"value": v, "name": re.sub(r"[^a-z0-9]+", "_", lbl.lower()).strip("_"),
         "title": lbl, "color_hint": c.lstrip("#").upper()}
    if v == NODATA:
        d["nodata"] = True
    return d


def classes(key):
    """The guide's value table as classification classes. For a continuous
    layer only the coded values and the two ends of the range are listed."""
    p = PRODUCTS[key]
    out = [_cls(v, c, lbl) for v, c, lbl in p["values"]]
    out += [_cls(v, c, lbl) for v, c, _, lbl in (p["ramp"] or [])]
    return sorted(out, key=lambda c: c["value"])


def classified(key):
    """Asset-level fields: nodata and the class list sit on the asset (one band)."""
    return {"nodata": NODATA, "classification:classes": classes(key)}


def band(key):
    p = PRODUCTS[key]
    b = {"name": p["band"], "description": p["summary"], "data_type": "uint8", "nodata": NODATA,
         "raster:bits_per_sample": 8, "raster:sampling": "area"}
    if p["unit"]:
        b["unit"] = p["unit"]
    return b


def render(key, asset):
    return {"title": PRODUCTS[key]["title"], "assets": [asset], "nodata": NODATA,
            "colormap": colormap(key)}


def metadata_yaml(cdir, key, ntiles):
    p = PRODUCTS[key]
    lo, hi = p["interval"]
    m = {
        "title": p["title"],
        "description": (
            f"{p['summary']} From the [GSW v1.5 Data Users Guide]({GUIDE}): \"{p['guide']}\" "
            f"The collection holds the {ntiles} upstream 10° × 10° tiles as items, copied byte for byte "
            f"(0.00025° grid, EPSG:4326, uint8, nodata {NODATA}), and one global overview COG at 0.004° "
            f"for display. Read [AGENTS.md](AGENTS.md) for access patterns."),
        "processing_notes": (
            f"Tiles copied unchanged from `{UPSTREAM}/{key}/`. The overview "
            f"(`{key}-overview.tif`) resamples each tile from the full-resolution pixels with "
            f"`{RESAMPLING[key]}` to 0.004°, mosaics them, and sets nodata {NODATA}. "
            f"Coverage: {lo[:10]} to {hi[:10]}."),
    }
    (cdir / ".portolan").mkdir(exist_ok=True)
    (cdir / ".portolan" / "metadata.yaml").write_text(
        "# Written by tools/stac.py from tools/products.py. Edit those, not this file.\n"
        + yaml.safe_dump(m, sort_keys=False, allow_unicode=True, width=100))


def item(cdir, key, t, src, size):
    p = PRODUCTS[key]
    bb = tile_bbox(t)
    lo, hi = p["interval"]
    tif = cdir / t / f"{t}.tif"
    d = {
        "type": "Feature", "stac_version": "1.1.0",
        "stac_extensions": [EXT["file"], EXT["proj"], EXT["raster"], EXT["classification"], EXT["render"]],
        "id": t,
        "geometry": {"type": "Polygon", "coordinates": [[[bb[0], bb[1]], [bb[2], bb[1]], [bb[2], bb[3]],
                                                         [bb[0], bb[3]], [bb[0], bb[1]]]]},
        "bbox": bb,
        "properties": {
            "title": f"{p['title']}, tile {t}",
            "description": f"{p['title']} for 10° × 10° tile {t} (upper-left corner {t.replace('_', ', ')}).",
            "datetime": None, "start_datetime": lo, "end_datetime": hi,
            "proj:code": "EPSG:4326", "proj:shape": [40000, 40000],
            "proj:transform": [RES, 0, bb[0], 0, -RES, bb[3]],
            "renders": {"default": render(key, "data")},
        },
        "links": [
            {"rel": "root", "href": "../../catalog.json", "type": "application/json"},
            {"rel": "parent", "href": "../collection.json", "type": "application/json"},
            {"rel": "collection", "href": "../collection.json", "type": "application/json"},
        ],
        "assets": {
            "data": {"href": f"./{t}.tif", "type": COG, "title": f"{p['title']} ({t})",
                     "roles": ["data"], "file:size": tif.stat().st_size, **classified(key),
                     "bands": [band(key)]},
            "source": {"href": f"{UPSTREAM}/{src}", "type": COG, "title": "Upstream original (CloudFerro)",
                       "description": "The object this tile was copied from, byte for byte. The host sends no CORS headers.",
                       "roles": ["source"], "file:size": size},
        },
        "collection": key,
    }
    save(cdir / t / f"{t}.json", d)
    return d


def style(cdir, key):
    """A MapLibre style over the overview COG, read with the cog:// protocol
    (maplibre-cog-protocol), which draws the embedded colour table."""
    p = PRODUCTS[key]
    url = f"cog://{PUBLIC}/{key}/{key}-overview.tif"
    s = {
        "version": 8, "name": p["title"],
        "metadata": {"portolan:description": f"{p['title']} from the global overview COG, in the Data Users Guide colours. "
                     "Not water and nodata are transparent. Needs maplibre-cog-protocol for cog:// sources."},
        "sources": {
            "basemap": {"type": "raster", "tileSize": 256, "attribution": "Esri, HERE, Garmin, (c) OpenStreetMap contributors",
                        "tiles": ["https://services.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Light_Gray_Base/MapServer/tile/{z}/{y}/{x}"]},
            key: {"type": "raster", "url": url, "tileSize": 256, "attribution": "Source: EC JRC/Google"},
        },
        "layers": [
            {"id": "basemap", "type": "raster", "source": "basemap"},
            {"id": key, "type": "raster", "source": key, "paint": {"raster-resampling": "nearest"}},
        ],
    }
    save(cdir / "style.json", s)


def collection(cat, key, tiles, root_meta, now):
    p = PRODUCTS[key]
    cdir = cat / key
    metadata_yaml(cdir, key, len(tiles))
    links = [
        {"rel": "root", "href": "../catalog.json", "type": "application/json"},
        {"rel": "parent", "href": "../catalog.json", "type": "application/json"},
    ]
    for t, src, size in tiles:
        item(cdir, key, t, src, size)
        links.append({"rel": "item", "href": f"./{t}/{t}.json", "type": "application/geo+json",
                      "title": f"Tile {t}"})
    links += [
        {"rel": "license", "href": root_meta["license_url"], "type": "text/html", "title": "CC BY 4.0"},
        {"rel": "via", "href": DOWNLOAD_PAGE, "type": "text/html", "title": "Global Surface Water Explorer: Data Access"},
        {"rel": "describedby", "href": "./README.md", "type": "text/markdown", "title": "Human-readable documentation"},
        {"rel": "agents", "href": "./AGENTS.md", "type": "text/markdown", "title": "Agent/LLM usage guide"},
        {"rel": "cite-as", "href": "https://doi.org/10.1038/nature20584", "type": "text/html",
         "title": "Pekel et al. (2016), Nature 540, 418-422"},
    ]
    lo, hi = p["interval"]
    ov = cdir / f"{key}-overview.tif"
    assets = {}
    if ov.exists():
        assets["overview"] = {
            "href": f"./{key}-overview.tif", "type": COG, "title": f"{p['title']}: global overview (0.004°)",
            "description": (f"Mosaic of all tiles resampled to 0.004° with `{RESAMPLING[key]}`. "
                            "For maps of the whole world; use the item tiles for analysis."),
            "roles": ["overview", "visual"], "file:size": ov.stat().st_size,
            "proj:code": "EPSG:4326", "proj:shape": [35000, 90000],
            "proj:transform": [0.004, 0, -180, 0, -0.004, 80], **classified(key), "bands": [band(key)],
        }
        style(cdir, key)
        assets["style"] = {"href": "./style.json", "type": "application/vnd.mapbox.style+json",
                           "title": f"{p['title']} (Data Users Guide colours)",
                           "roles": ["style", "default"], "file:size": (cdir / "style.json").stat().st_size}
    th = cdir / "thumbnail.png"
    if th.exists():
        assets["thumbnail"] = {"href": "./thumbnail.png", "type": "image/png", "title": "Thumbnail",
                               "description": f"{p['title']}, whole layer, over Esri World Light Gray. Rendered by tools/make_thumbs.py.",
                               "roles": ["thumbnail"], "file:size": th.stat().st_size}
    old = load(cdir / "collection.json") if (cdir / "collection.json").exists() else {}
    if "geoparquet-items" in old.get("assets", {}):
        assets["geoparquet-items"] = old["assets"]["geoparquet-items"]
        assets["geoparquet-items"].update(
            title="Item index",
            description="STAC GeoParquet copy of every item in this collection, one row per tile. The item JSON is normative.")
    c = {
        "type": "Collection", "id": key, "stac_version": "1.1.0",
        "stac_extensions": [EXT["file"], EXT["proj"], EXT["raster"], EXT["classification"], EXT["render"],
                            EXT["item_assets"], PORTOLAN],
        "title": p["title"],
        "description": yaml.safe_load((cdir / ".portolan" / "metadata.yaml").read_text())["description"],
        "license": root_meta["license"],
        "providers": root_meta["providers"],
        "extent": {"spatial": {"bbox": [[-180, -60, 180, 80]]}, "temporal": {"interval": [[lo, hi]]}},
        "summaries": {"proj:code": ["EPSG:4326"], "raster:spatial_resolution": [RES]},
        "item_assets": {
            "data": {"type": COG, "roles": ["data"], "title": p["title"], **classified(key), "bands": [band(key)]},
            "source": {"type": COG, "roles": ["source"], "title": "Upstream original (CloudFerro)"},
        },
        "renders": {"default": render(key, "overview" if ov.exists() else "data")},
        "assets": assets,
        "links": links,
        "updated": now,
    }
    save(cdir / "collection.json", c)
    return c


def root(cat, root_meta, now):
    r = load(cat / "catalog.json")
    r["id"] = "global-surface-water"
    r["title"] = root_meta["title"]
    r["description"] = " ".join(root_meta["description"].split())
    r["updated"] = now
    keep = [lnk for lnk in r["links"] if lnk["rel"] in ("root", "describedby", "agents")]
    r["links"] = keep + [
        {"rel": "child", "href": f"./{k}/collection.json", "type": "application/json", "title": PRODUCTS[k]["title"]}
        for k in PRODUCTS] + [
        {"rel": "self", "href": f"{PUBLIC}/catalog.json", "type": "application/json"},
        {"rel": "via", "href": DOWNLOAD_PAGE, "type": "text/html", "title": "Global Surface Water Explorer: Data Access"},
        {"rel": "vcs", "href": REPO, "type": "text/html", "title": "Build scripts and metadata"},
        {"rel": "issues", "href": f"{REPO}/issues", "type": "text/html", "title": "Report a problem"},
        {"rel": "icon", "href": "./_assets/logo.png", "type": "image/png",
         "title": "European Commission Joint Research Centre"},
    ]
    save(cat / "catalog.json", r)


def main():
    cat = Path(sys.argv[1]).resolve()
    manifest = load(sys.argv[2])["tiles"]
    root_meta = yaml.safe_load((cat / ".portolan" / "metadata.yaml").read_text())
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    for key in PRODUCTS:
        tiles = sorted((re.match(rf"{key}_(\d+[EW]_\d+[NS])_", n.split("/")[1])[1], n, v["bytes"])
                       for n, v in manifest.items() if n.startswith(key + "/"))
        missing = [t for t, _, _ in tiles if not (cat / key / t / f"{t}.tif").exists()]
        assert not missing, f"{key}: {len(missing)} tiles missing, e.g. {missing[:3]}"
        collection(cat, key, tiles, root_meta, now)
    root(cat, root_meta, now)


main()
