# AGENTS.md: Water transitions

Change in seasonality between the first and last year of observation: ten classes of water transition. Band `transition`, uint8, 1984-03-16 to 2024-12-31. The
[catalog guide](../AGENTS.md) covers the tile layout, nodata, and the traps
every layer shares.

## Values

From the [Data Users Guide](https://storage.googleapis.com/water-world/downloads_ancillary/DataUsersGuidev2024_v.5.pdf):

| Value | Meaning |
|---|---|
| `0` | Not water |
| `1` | Permanent |
| `2` | New permanent |
| `3` | Lost permanent |
| `4` | Seasonal |
| `5` | New seasonal |
| `6` | Lost seasonal |
| `7` | Seasonal to permanent |
| `8` | Permanent to seasonal |
| `9` | Ephemeral permanent |
| `10` | Ephemeral seasonal |
| `255` | No data |

## Reading the values

- Classes compare the first and last representative years only. The guide: they "do not describe what happened in the intervening years".
- `9` and `10` (ephemeral) are pixels with water in some middle years but not at either end.
- Class titles are in the STAC `classification:classes` of the data asset, so a client can label pixels without this table (recipe below).

## Overview

`transitions-overview.tif` is resampled with `mode`. Each coarse pixel takes the most common value, so features narrower than a coarse pixel (0.004°, about 445 m at the equator) can vanish.

## Recipes

The value at the former bed of the Aral Sea (59.6, 45.0), from tile `50E_50N`:

```bash
gdallocationinfo -valonly -wgs84 "/vsicurl/https://data.source.coop/portolan-mirrors/global-surface-water/transitions/50E_50N/50E_50N.tif" 59.6 45.0
# 3
```

Label a class from the item index instead of hard-coding the table:

```sql
SELECT c.value, c.title
FROM (SELECT unnest(assets.data."classification:classes") AS c
      FROM read_parquet('https://data.source.coop/portolan-mirrors/global-surface-water/transitions/items.parquet') WHERE id = '50E_50N')
WHERE c.value = 3;
-- 3  Lost permanent
```
