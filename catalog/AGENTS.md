# AGENTS.md: Global Surface Water Explorer v1.5

A mirror of the six aggregated layers of the JRC/Google Global Surface Water
Explorer v1.5 (1984 to 2024). Public root: `https://data.source.coop/portolan-mirrors/global-surface-water/catalog.json`.
Upstream: the [download page](https://global-surface-water.appspot.com/download) and its
[Data Users Guide](https://storage.googleapis.com/water-world/downloads_ancillary/DataUsersGuidev2024_v.5.pdf).

**One rule survives every edit to this file.** Every claim here is either quoted
from a source or measured from the data. Every number below comes from the
Data Users Guide or from a query in this file, which a weekly job reruns
against the published objects.

## What this catalog holds

| Collection | Title | Band | What a pixel means |
|---|---|---|---|
| [`occurrence`](occurrence/AGENTS.md) | Water occurrence | `occurrence` | How often surface water was present, March 1984 to December 2024, as a percentage of valid observations. |
| [`change`](change/AGENTS.md) | Occurrence change intensity | `change_norm` | Change in water occurrence between 1984-1999 and 2000-2024, from homologous months. 100 is no change. |
| [`seasonality`](seasonality/AGENTS.md) | Seasonality | `seasonality` | Number of months in the year that water was present; 12 is permanent water. |
| [`recurrence`](recurrence/AGENTS.md) | Water recurrence | `recurrence` | How often water returned from year to year, as a percentage of observation years within each pixel's water period. |
| [`transitions`](transitions/AGENTS.md) | Water transitions | `transition` | Change in seasonality between the first and last year of observation: ten classes of water transition. |
| [`extent`](extent/AGENTS.md) | Maximum water extent | `max_extent` | Every location ever detected as water, 1984 to 2024. |

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
https://data.source.coop/portolan-mirrors/global-surface-water/<layer>/<tile>/<tile>.tif
```

A tile id is the **upper-left** corner: `100E_20N` covers 100 E to 110 E and
10 N to 20 N. Find the tile for a point from the item index instead of
computing it:

```sql
SELECT id
FROM read_parquet('https://data.source.coop/portolan-mirrors/global-surface-water/occurrence/items.parquet')
WHERE bbox.xmin <= 104.05 AND bbox.xmax > 104.05
  AND bbox.ymin <= 12.85 AND bbox.ymax > 12.85;
-- 100E_20N
```

Read a window without downloading the tile: Tonle Sap lake, about 1° x 0.8°
of occurrence. GDAL fetches only the blocks it needs. QGIS does the same when
you add the URL with the `/vsicurl/` prefix (Layer, Add Raster Layer,
Protocol: HTTP(S)).

```bash
gdal_translate -q -a_nodata 255 -projwin 103.6 13.2 104.6 12.4 \
  /vsicurl/https://data.source.coop/portolan-mirrors/global-surface-water/occurrence/100E_20N/100E_20N.tif tonle.tif
gdalinfo -stats tonle.tif | grep -E 'Size is|STATISTICS_MAXIMUM'
# Size is 4000, 3200
#     STATISTICS_MAXIMUM=100
```

For a whole continent or the world, read the overview of a layer,
`https://data.source.coop/portolan-mirrors/global-surface-water/<layer>/<layer>-overview.tif` (0.004°, about 445 m at the
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
