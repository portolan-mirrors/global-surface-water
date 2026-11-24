# Global Surface Water Explorer v1.5

![surface water](https://img.shields.io/badge/surface_water-blue) ![hydrology](https://img.shields.io/badge/hydrology-blue) ![water occurrence](https://img.shields.io/badge/water_occurrence-blue) ![wetlands](https://img.shields.io/badge/wetlands-blue) ![Landsat](https://img.shields.io/badge/Landsat-blue) ![Copernicus](https://img.shields.io/badge/Copernicus-blue) ![JRC](https://img.shields.io/badge/JRC-blue)

A mirror of the aggregated layers of the [Global Surface Water Explorer](https://global-surface-water.appspot.com/) v1.5 (1984 to 2024), produced by the European Commission Joint Research Centre (JRC) with Google. The layers map where and when surface water occurred on land from March 1984 to December 2024, from the Landsat archive at a 0.00025° (about 30 m) grid. The catalog holds six collections, one per layer: occurrence, occurrence change intensity, seasonality, recurrence, transitions, and maximum extent. Each collection has the 504 upstream 10° × 10° cloud-optimized GeoTIFF tiles, copied byte for byte, plus one global overview COG for maps of the whole world. Read [AGENTS.md](AGENTS.md) before you query.

## Collections

### [Occurrence change intensity](change/README.md)

Change in water occurrence between 1984-1999 and 2000-2024, from homologous months. 100 is no change. From the [GSW v1.5 Data Users Guide](https://storage.googleapis.com/water-world/downloads_ancil...

### [Maximum water extent](extent/README.md)

Every location ever detected as water, 1984 to 2024. From the [GSW v1.5 Data Users Guide](https://storage.googleapis.com/water-world/downloads_ancillary/DataUsersGuidev2024_v.5.pdf): "The Maximum W...

### [Water occurrence](occurrence/README.md)

How often surface water was present, March 1984 to December 2024, as a percentage of valid observations. From the [GSW v1.5 Data Users Guide](https://storage.googleapis.com/water-world/downloads_an...

### [Water recurrence](recurrence/README.md)

How often water returned from year to year, as a percentage of observation years within each pixel's water period. From the [GSW v1.5 Data Users Guide](https://storage.googleapis.com/water-world/do...

### [Seasonality](seasonality/README.md)

Number of months in the year that water was present; 12 is permanent water. From the [GSW v1.5 Data Users Guide](https://storage.googleapis.com/water-world/downloads_ancillary/DataUsersGuidev2024_v...

### [Water transitions](transitions/README.md)

Change in seasonality between the first and last year of observation: ten classes of water transition. From the [GSW v1.5 Data Users Guide](https://storage.googleapis.com/water-world/downloads_anci...

## Coverage

**Spatial Extent**

- West: -180.0000, South: -60.0000, East: 180.0000, North: 80.0000

**Temporal Extent**

- 1984-03-16 to 2024-12-31

## Source

[https://global-surface-water.appspot.com/download](https://global-surface-water.appspot.com/download)

## Processing Notes

The 3,024 tiles (six layers × 504 tiles) under `download2024/Aggregated/VER1-5/` of the public CloudFerro bucket that the [download page](https://global-surface-water.appspot.com/download) links for V1.5 were copied unchanged; the MD5 of every copy matches the hash the bucket lists. The occurrence folder holds each tile twice under two names (`occurrence_<tile>_v1_5_2024.tif` and `<tile>_p41_Occurrence.tif`); only the first name was copied. The tiles carry no NoData tag; the STAC metadata records 255 as nodata, the "No data" value in the Data Users Guide. The global overview COG of each layer is the only derived file: a mosaic of the tiles resampled to 0.004° (16 × coarser), with nodata 255 set and a colour table built from the Data Users Guide colours, in which "not water" and nodata are transparent. Occurrence and recurrence are averaged; seasonality, change, and transitions take the most common value (mode); extent takes the maximum. Use the tiles for analysis, and the overviews only for display. The build scripts are in [the repository](https://github.com/portolan-mirrors/global-surface-water).

## Citation

Jean-Francois Pekel, Andrew Cottam, Noel Gorelick, Alan S. Belward, High-resolution mapping of global surface water and its long-term changes. Nature 540, 418-422 (2016). doi:10.1038/nature20584

## Attribution

© European Union, 1995-2021. Source: EC JRC/Google. Licensed under CC BY 4.0 per the [JRC copyright notice](https://jeodpp.jrc.ec.europa.eu/ftp/jrc-opendata/GSWE/copyright.txt): reuse is allowed "provided appropriate credit is given and any changes are indicated". Changes in this mirror: none to the tiles; the global overview COGs are resampled and recoloured (see Processing Notes). The [download page](https://global-surface-water.appspot.com/download) asks that publications cite the dataset and Pekel et al. (2016), and that maps credit "Source: EC JRC/Google".

## License

[CC-BY-4.0](https://creativecommons.org/licenses/by/4.0/)

## Contact

Portolan Mirrors <nissim@radiant.earth>

---

*Generated by [Portolan](https://github.com/portolan-sdi/portolan-cli) from STAC metadata and .portolan/metadata.yaml*
