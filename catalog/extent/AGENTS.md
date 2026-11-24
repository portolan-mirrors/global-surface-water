# AGENTS.md: Maximum water extent

Every location ever detected as water, 1984 to 2024. Band `max_extent`, uint8, 1984-03-16 to 2024-12-31. The
[catalog guide](../AGENTS.md) covers the tile layout, nodata, and the traps
every layer shares.

## Values

From the [Data Users Guide](https://storage.googleapis.com/water-world/downloads_ancillary/DataUsersGuidev2024_v.5.pdf):

| Value | Meaning |
|---|---|
| `0` | Not water |
| `1` | Water detected |
| `255` | No data |

## Reading the values

- The guide: "the union of all the other datasets". A pixel is `1` if water was detected even once in 41 years.
- Extent is a flag, so it cannot tell a permanent lake from a single flood. Use `occurrence` for how often.

## Overview

`extent-overview.tif` is resampled with `max`. Each coarse pixel is 1 if any fine pixel is, so water looks wider than it is.

## Recipes

The value at the Amazon near Manaus, Brazil (-59.6641, -3.1684), from tile `60W_0N`:

```bash
gdallocationinfo -valonly -wgs84 "/vsicurl/https://data.source.coop/portolan-mirrors/global-surface-water/extent/60W_0N/60W_0N.tif" -59.6641 -3.1684
# 1
```
