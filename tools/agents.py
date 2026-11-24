#!/usr/bin/env python3
"""Write catalog/AGENTS.md and catalog/<product>/AGENTS.md.

Value tables come from tools/products.py (the Data Users Guide). Every other
number sits in a fence that tests/test_agent_claims.py runs against the
published objects; the comment lines in a fence are its checked output.

    python3 -I tools/agents.py catalog
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from products import DOWNLOAD_PAGE, GUIDE, NODATA, PRODUCTS, PUBLIC, RESAMPLING  # noqa: E402

CAT = Path(sys.argv[1]).resolve()

# One example pixel per layer, inside the layer's thumbnail frame. Values
# were measured from the tiles; the fences below re-check them weekly.
EXAMPLE = {
    "occurrence": (104.05, 12.85, "100E_20N", "93", "Tonle Sap, Cambodia"),
    "change": (90.0136, 26.0631, "90E_30N", "30", "the Brahmaputra floodplain, Assam"),
    "seasonality": (-4.00, 15.20, "10W_20N", "6", "the Inner Niger Delta, Mali"),
    "recurrence": (-90.6406, 35.3941, "100W_40N", "34", "the Mississippi floodplain, Arkansas"),
    "transitions": (59.60, 45.00, "50E_50N", "3", "the former bed of the Aral Sea"),
    "extent": (-59.6641, -3.1684, "60W_0N", "1", "the Amazon near Manaus, Brazil"),
}
TONLE_SAP = EXAMPLE["occurrence"][:3]

# Layer-specific reading notes. Quotes are from the Data Users Guide.
NOTES = {
    "occurrence": [
        "The value is a percentage of valid observations that saw water, computed per calendar month and then averaged, "
        "so a wet season with few cloud-free scenes is not under-weighted. The guide: \"The month-by-month time step "
        "normalizes occurrence against seasonal variation in the number of valid observations across the year.\"",
        "`100` is water in every valid observation; the guide calls it \"permanent water surfaces (100% occurrence)\".",
        "Occurrence says how often, not when. Use `transitions` or `change` for direction over time.",
    ],
    "change": [
        "The tile value is offset by 100: percent change = value - 100, so `0` is -100% and `200` is +100%. Earth Engine "
        "serves the same band already offset (the guide's \"Value (GEE)\" column).",
        "`253` (not water) and `254` (no homologous months) are codes, not changes. Mask both before any arithmetic.",
        "The two epochs are 16 March 1984 to 31 December 1999 and 1 January 2000 to 31 December 2024. Only months "
        "observed in both epochs count, so a pixel's change can rest on a few months.",
    ],
    "seasonality": [
        "The value is a count of months with water in one year, from 2022 to 2024 (guide: \"only cover the 2022-2024 "
        "period\"). `12` is permanent water.",
        "Ice counts as no observation: \"If water is present throughout the observation period (that is, the unfrozen "
        "period), the lake is considered to be a permanent water surface.\" Frozen lakes therefore read as permanent.",
    ],
    "recurrence": [
        "The value is the share of observation years with water, counted only inside each pixel's own water period "
        "(first to last year with water) and water season. Two pixels with the same value can cover different years.",
        "Recurrence is about return from year to year; a pixel flooded briefly every year scores `100`.",
    ],
    "transitions": [
        "Classes compare the first and last representative years only. The guide: they \"do not describe what happened "
        "in the intervening years\".",
        "`9` and `10` (ephemeral) are pixels with water in some middle years but not at either end.",
        "Class titles are in the STAC `classification:classes` of the data asset, so a client can label pixels without "
        "this table (recipe below).",
    ],
    "extent": [
        "The guide: \"the union of all the other datasets\". A pixel is `1` if water was detected even once in 41 years.",
        "Extent is a flag, so it cannot tell a permanent lake from a single flood. Use `occurrence` for how often.",
    ],
}

# Extra fences per layer: (intro, fence language, body). {url} is the layer URL.
EXTRA = {
    "change": ("Convert the tile value to percent change in occurrence:", "bash",
               'v=$(gdallocationinfo -valonly -wgs84 "/vsicurl/{url}/90E_30N/90E_30N.tif" 90.0136 26.0631)\n'
               'echo "value $v, change $((v - 100))%"\n# value 30, change -70%'),
    "transitions": ("Label a class from the item index instead of hard-coding the table:", "sql",
                    "SELECT c.value, c.title\n"
                    "FROM (SELECT unnest(assets.data.\"classification:classes\") AS c\n"
                    "      FROM read_parquet('{url}/items.parquet') WHERE id = '50E_50N')\n"
                    "WHERE c.value = 3;\n-- 3  Lost permanent"),
}


def value_table(key):
    p = PRODUCTS[key]
    rows = [(v, lbl) for v, _, lbl in p["values"]]
    if p["ramp"]:
        r = p["ramp"]
        rows += [(f"{r[0][0]}-{r[-1][0]}", f"{r[0][3]} to {r[-1][3]}")]
    rows.sort(key=lambda r: int(str(r[0]).split("-")[0]))
    return "| Value | Meaning |\n|---|---|\n" + "\n".join(f"| `{v}` | {lbl} |" for v, lbl in rows)


def collection_guide(key):
    p = PRODUCTS[key]
    lo, hi = p["interval"]
    lon, lat, tile, val, place = EXAMPLE[key]
    url = f"{PUBLIC}/{key}"
    notes = "\n".join(f"- {n}" for n in NOTES[key])
    extra = ""
    if key in EXTRA:
        intro, lang, body = EXTRA[key]
        extra = f"\n{intro}\n\n```{lang}\n{body.format(url=url)}\n```\n"
    return f"""# AGENTS.md: {p['title']}

{p['summary']} Band `{p['band']}`, uint8, {lo[:10]} to {hi[:10]}. The
[catalog guide](../AGENTS.md) covers the tile layout, nodata, and the traps
every layer shares.

## Values

From the [Data Users Guide]({GUIDE}):

{value_table(key)}

## Reading the values

{notes}

## Overview

`{key}-overview.tif` is resampled with `{RESAMPLING[key]}`. {"Averaging smooths the percentages, so a thin river reads lower than it is." if RESAMPLING[key] == "average" else "Each coarse pixel takes the most common value, so features narrower than a coarse pixel (0.004°, about 445 m at the equator) can vanish." if RESAMPLING[key] == "mode" else "Each coarse pixel is 1 if any fine pixel is, so water looks wider than it is."}

## Recipes

The value at {place} ({lon}, {lat}), from tile `{tile}`:

```bash
gdallocationinfo -valonly -wgs84 "/vsicurl/{url}/{tile}/{tile}.tif" {lon} {lat}
# {val}
```
{extra}"""


def root_guide():
    rows = "\n".join(f"| [`{k}`]({k}/AGENTS.md) | {p['title']} | `{p['band']}` | {p['summary']} |"
                     for k, p in PRODUCTS.items())
    return f"""# AGENTS.md: Global Surface Water Explorer v1.5

A mirror of the six aggregated layers of the JRC/Google Global Surface Water
Explorer v1.5 (1984 to 2024). Public root: `{PUBLIC}/catalog.json`.
Upstream: the [download page]({DOWNLOAD_PAGE}) and its
[Data Users Guide]({GUIDE}).

**One rule survives every edit to this file.** Every claim here is either quoted
from a source or measured from the data. Every number below comes from the
Data Users Guide or from a query in this file, which a weekly job reruns
against the published objects.

## What this catalog holds

| Collection | Title | Band | What a pixel means |
|---|---|---|---|
{rows}

Each collection holds 504 items, one per 10° x 10° tile, from 180 W to 180 E
and 80 N to 60 S, plus one global overview COG for display.

## Uses and limits

- **Intended uses.** The producer's site says the dataset "will support
  applications including water resource management, climate modelling,
  biodiversity conservation and food security", and that JRC, UN Environment
  and Google built a [dedicated interface](https://global-surface-water.appspot.com/)
  on it for SDG indicator 6.6.1.
- **Accuracy.** The 2026 Data Users Guide separates "the original 1984 to
  2015 period, presented in the above paper and thoughtfully validated" from
  "the extensions to cover the 2016-2021 and 2022-2024 periods". The
  validation (omission and commission protocols) is in
  [Pekel et al. 2016](https://doi.org/10.1038/nature20584), Extended Data
  Figures 4 and 5. The guide gives no validation for the extensions, and this
  mirror publishes no accuracy figures of its own.
- **Observation bias.** Results depend on cloud-free Landsat views. The
  guide: "more cloud-free observations (and thus valid observations) are
  available during dry seasons than wet". Occurrence corrects for this month
  by month; the other layers inherit it. Ice is a non-valid observation, so
  frozen months are missing.
- **Not for flood mapping of single events.** Every layer aggregates 1984 to
  2024 (seasonality: 2022 to 2024). None says where water was on a given
  date. For that, the producer's monthly history (not mirrored here) is the
  source.
- **Display, not analysis, for the overviews.** Analyse the tiles; the
  overviews are resampled. For display only, the guide recommends the
  producer's WMTS service, "the fastest to load".

## How to read it

The tile URL pattern, with `<layer>` a collection id above:

```text
{PUBLIC}/<layer>/<tile>/<tile>.tif
```

A tile id is the **upper-left** corner: `100E_20N` covers 100 E to 110 E and
10 N to 20 N. Find the tile for a point from the item index instead of
computing it:

```sql
SELECT id
FROM read_parquet('{PUBLIC}/occurrence/items.parquet')
WHERE bbox.xmin <= {TONLE_SAP[0]} AND bbox.xmax > {TONLE_SAP[0]}
  AND bbox.ymin <= {TONLE_SAP[1]} AND bbox.ymax > {TONLE_SAP[1]};
-- 100E_20N
```

Read a window without downloading the tile: Tonle Sap lake, about 1° x 0.8°
of occurrence. GDAL fetches only the blocks it needs. QGIS does the same when
you add the URL with the `/vsicurl/` prefix (Layer, Add Raster Layer,
Protocol: HTTP(S)).

```bash
gdal_translate -q -a_nodata {NODATA} -projwin 103.6 13.2 104.6 12.4 \\
  /vsicurl/{PUBLIC}/occurrence/100E_20N/100E_20N.tif tonle.tif
gdalinfo -stats tonle.tif | grep -E 'Size is|STATISTICS_MAXIMUM'
# Size is 4000, 3200
#     STATISTICS_MAXIMUM=100
```

For a whole continent or the world, read the overview of a layer,
`{PUBLIC}/<layer>/<layer>-overview.tif` (0.004°, about 445 m at the
equator). It is resampled, so do not compute areas from it.

## Join keys

All six layers share one grid: the same 504 tile ids and the same 0.00025°
pixel grid. Pixel (row, col) of tile `T` in one layer is the same place as
pixel (row, col) of tile `T` in every other layer. Nothing else joins.

## Quirks that produce silently wrong answers

- **No NoData tag.** The tiles are the upstream bytes, and upstream sets no
  NoData value. `255` means no data in every layer (Data Users Guide). GDAL,
  QGIS, and rasterio treat it as a valid value unless you set it. The STAC
  `bands` and the overviews do set 255.
- **`0` is "not water", not no data,** except in `change`, where `0` is
  "-100% loss of occurrence" and `253` is not water. `change` also has `254`
  for "unable to calculate a value due to no homologous months".
- **`change` has one band.** The Data Users Guide lists `change_abs` and
  `change_norm`; the downloadable tiles hold one band that matches the
  `change_norm` value table (100 = no change).
- **Seasonality covers only 2022 to 2024.** The guide: "the Seasonality,
  Monthly History, and Yearly History assets only cover the 2022-2024 period".
- **Collection 1 and Collection 2.** From 2022 the source imagery is Landsat
  Collection 2. The guide says combining it with Collection 1 "introduces a
  residual co-registration offset", typically sub-pixel but up to about one
  30 m pixel in some WRS-2 path/rows.
- **Pixels are not square in metres.** 0.00025° is about 27.8 m at the
  equator and narrower east-west toward the poles. Reproject before you
  measure areas.
- **Upstream `source` assets** point at CloudFerro, which sends no CORS
  headers. Read the copies here from a browser.

## Structure

Assets and structural links resolve relative to the object that carries
them. The root `catalog.json` carries an absolute `self` link.
"""


def main():
    (CAT / "AGENTS.md").write_text(root_guide())
    for key in PRODUCTS:
        (CAT / key / "AGENTS.md").write_text(collection_guide(key))


main()
