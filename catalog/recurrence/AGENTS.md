# AGENTS.md: Water recurrence

How often water returned from year to year, as a percentage of observation years within each pixel's water period. Band `recurrence`, uint8, 1984-03-16 to 2024-12-31. The
[catalog guide](../AGENTS.md) covers the tile layout, nodata, and the traps
every layer shares.

## Values

From the [Data Users Guide](https://storage.googleapis.com/water-world/downloads_ancillary/DataUsersGuidev2024_v.5.pdf):

| Value | Meaning |
|---|---|
| `0` | Not water |
| `1-100` | 1% recurrence to 100% recurrence |
| `255` | No data |

## Reading the values

- The value is the share of observation years with water, counted only inside each pixel's own water period (first to last year with water) and water season. Two pixels with the same value can cover different years.
- Recurrence is about return from year to year; a pixel flooded briefly every year scores `100`.

## Overview

`recurrence-overview.tif` is resampled with `average`. Averaging smooths the percentages, so a thin river reads lower than it is.

## Recipes

The value at the Mississippi floodplain, Arkansas (-90.6406, 35.3941), from tile `100W_40N`:

```bash
gdallocationinfo -valonly -wgs84 "/vsicurl/https://data.source.coop/portolan-mirrors/global-surface-water/recurrence/100W_40N/100W_40N.tif" -90.6406 35.3941
# 34
```
