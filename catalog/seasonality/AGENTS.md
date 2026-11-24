# AGENTS.md: Seasonality

Number of months in the year that water was present; 12 is permanent water. Band `seasonality`, uint8, 2022-01-01 to 2024-12-31. The
[catalog guide](../AGENTS.md) covers the tile layout, nodata, and the traps
every layer shares.

## Values

From the [Data Users Guide](https://storage.googleapis.com/water-world/downloads_ancillary/DataUsersGuidev2024_v.5.pdf):

| Value | Meaning |
|---|---|
| `0` | Not water |
| `1-12` | 1 month of water to 12 months of water (permanent water) |
| `255` | No data |

## Reading the values

- The value is a count of months with water in one year, from 2022 to 2024 (guide: "only cover the 2022-2024 period"). `12` is permanent water.
- Ice counts as no observation: "If water is present throughout the observation period (that is, the unfrozen period), the lake is considered to be a permanent water surface." Frozen lakes therefore read as permanent.

## Overview

`seasonality-overview.tif` is resampled with `mode`. Each coarse pixel takes the most common value, so features narrower than a coarse pixel (0.004°, about 445 m at the equator) can vanish.

## Recipes

The value at the Inner Niger Delta, Mali (-4.0, 15.2), from tile `10W_20N`:

```bash
gdallocationinfo -valonly -wgs84 "/vsicurl/https://data.source.coop/portolan-mirrors/global-surface-water/seasonality/10W_20N/10W_20N.tif" -4.0 15.2
# 6
```
