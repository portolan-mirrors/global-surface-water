# AGENTS.md: Occurrence change intensity

Change in water occurrence between 1984-1999 and 2000-2024, from homologous months. 100 is no change. Band `change_norm`, uint8, 1984-03-16 to 2024-12-31. The
[catalog guide](../AGENTS.md) covers the tile layout, nodata, and the traps
every layer shares.

## Values

From the [Data Users Guide](https://storage.googleapis.com/water-world/downloads_ancillary/DataUsersGuidev2024_v.5.pdf):

| Value | Meaning |
|---|---|
| `0-200` | -100% loss of occurrence to 100% increase in occurrence |
| `253` | Not water |
| `254` | Unable to calculate a value due to no homologous months |
| `255` | No data |

## Reading the values

- The tile value is offset by 100: percent change = value - 100, so `0` is -100% and `200` is +100%. Earth Engine serves the same band already offset (the guide's "Value (GEE)" column).
- `253` (not water) and `254` (no homologous months) are codes, not changes. Mask both before any arithmetic.
- The two epochs are 16 March 1984 to 31 December 1999 and 1 January 2000 to 31 December 2024. Only months observed in both epochs count, so a pixel's change can rest on a few months.

## Overview

`change-overview.tif` is resampled with `mode`. Each coarse pixel takes the most common value, so features narrower than a coarse pixel (0.004°, about 445 m at the equator) can vanish.

## Recipes

The value at the Brahmaputra floodplain, Assam (90.0136, 26.0631), from tile `90E_30N`:

```bash
gdallocationinfo -valonly -wgs84 "/vsicurl/https://data.source.coop/portolan-mirrors/global-surface-water/change/90E_30N/90E_30N.tif" 90.0136 26.0631
# 30
```

Convert the tile value to percent change in occurrence:

```bash
v=$(gdallocationinfo -valonly -wgs84 "/vsicurl/https://data.source.coop/portolan-mirrors/global-surface-water/change/90E_30N/90E_30N.tif" 90.0136 26.0631)
echo "value $v, change $((v - 100))%"
# value 30, change -70%
```
