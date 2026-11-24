# AGENTS.md: Water occurrence

How often surface water was present, March 1984 to December 2024, as a percentage of valid observations. Band `occurrence`, uint8, 1984-03-16 to 2024-12-31. The
[catalog guide](../AGENTS.md) covers the tile layout, nodata, and the traps
every layer shares.

## Values

From the [Data Users Guide](https://storage.googleapis.com/water-world/downloads_ancillary/DataUsersGuidev2024_v.5.pdf):

| Value | Meaning |
|---|---|
| `0` | Not water |
| `1-100` | 1% occurrence to 100% occurrence |
| `255` | No data |

## Reading the values

- The value is a percentage of valid observations that saw water, computed per calendar month and then averaged, so a wet season with few cloud-free scenes is not under-weighted. The guide: "The month-by-month time step normalizes occurrence against seasonal variation in the number of valid observations across the year."
- `100` is water in every valid observation; the guide calls it "permanent water surfaces (100% occurrence)".
- Occurrence says how often, not when. Use `transitions` or `change` for direction over time.

## Overview

`occurrence-overview.tif` is resampled with `average`. Averaging smooths the percentages, so a thin river reads lower than it is.

## Recipes

The value at Tonle Sap, Cambodia (104.05, 12.85), from tile `100E_20N`:

```bash
gdallocationinfo -valonly -wgs84 "/vsicurl/https://data.source.coop/portolan-mirrors/global-surface-water/occurrence/100E_20N/100E_20N.tif" 104.05 12.85
# 93
```
