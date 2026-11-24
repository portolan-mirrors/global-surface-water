"""The six GSWE v1.5 aggregated products: one place for every per-product fact.

Every description, value, colour, and label below is copied from the
GSW v1.5 Data Users Guide (DataUsersGuidev2024_v.5.pdf, pages 3 to 12):
https://storage.googleapis.com/water-world/downloads_ancillary/DataUsersGuidev2024_v.5.pdf

The other tools (meta.py, finalize_stac.py, make_overview.py, styles.py,
make_thumbs.py) import from here, so a correction is made once.
"""

SLUG = "global-surface-water"
PUBLIC = f"https://data.source.coop/portolan-mirrors/{SLUG}"
REPO = f"https://github.com/portolan-mirrors/{SLUG}"
UPSTREAM = "https://s3.waw4-1.cloudferro.com/swift/v1/global-surface-water/download2024/Aggregated/VER1-5"
DOWNLOAD_PAGE = "https://global-surface-water.appspot.com/download"
GUIDE = "https://storage.googleapis.com/water-world/downloads_ancillary/DataUsersGuidev2024_v.5.pdf"

FULL = ("1984-03-16T00:00:00Z", "2024-12-31T23:59:59Z")
NODATA = 255

# Each value table is the guide's "Symbology" table. A `ramp` is a pair of
# end points the guide gives for a continuous range ("the values from 1 to
# 100 are discrete"), with the colours of those end points.
PRODUCTS = {
    "occurrence": {
        "title": "Water occurrence",
        "band": "occurrence",
        "unit": "percent",
        "kind": "continuous",
        "interval": FULL,
        "summary": "How often surface water was present, March 1984 to December 2024, as a percentage of valid observations.",
        "guide": (
            "The frequency with which water was present on the surface from March 1984 to December 2024 "
            "was captured in a single product called surface water occurrence (WO). To compute WO, the water "
            "detections (WD) and valid observations (VO) from the same months are summed [...] such that "
            "WOmonth = ∑WD month / ∑VO month. Averaging the results of all monthly WOmonth calculations gives "
            "the long-term overall surface water occurrence."
        ),
        "values": [(0, "#FFFFFF", "Not water"), (255, "#CCCCCC", "No data")],
        "ramp": [(1, "#FF0000", 0.01, "1% occurrence"), (100, "#0000FF", 1.0, "100% occurrence")],
    },
    "change": {
        "title": "Occurrence change intensity",
        "band": "change_norm",
        "unit": "percent change",
        "kind": "diverging",
        "interval": FULL,
        "summary": "Change in water occurrence between 1984-1999 and 2000-2024, from homologous months. 100 is no change.",
        "guide": (
            "Change in water occurrence intensity between two epochs (16 March 1984 to 31 December 1999, "
            "and 1 January 2000 to 31 December 2024) was also produced. This is derived from homologous pairs "
            "of months (that is, the same months contain valid observations in both epochs). [...] Areas where "
            "there are no pairs of homologue months could not be mapped."
        ),
        "values": [
            (253, "#FFFFFF", "Not water"),
            (254, "#888888", "Unable to calculate a value due to no homologous months"),
            (255, "#CCCCCC", "No data"),
        ],
        "ramp": [
            (0, "#FF0000", 1.0, "-100% loss of occurrence"),
            (100, "#000000", 1.0, "No change"),
            (200, "#00FF00", 1.0, "100% increase in occurrence"),
        ],
    },
    "seasonality": {
        "title": "Seasonality",
        "band": "seasonality",
        "unit": "months",
        "kind": "continuous",
        "interval": ("2022-01-01T00:00:00Z", "2024-12-31T23:59:59Z"),
        "summary": "Number of months in the year that water was present; 12 is permanent water.",
        "guide": (
            "The Seasonality map provides information concerning the intra-annual behaviour of water surfaces "
            "for a single year and shows permanent and seasonal water and the number of months water was present. "
            "A permanent water surface is underwater throughout the year, while a seasonal water surface is "
            "underwater for less than 12 months of the year."
        ),
        "values": [(0, "#FFFFFF", "Not water"), (255, "#CCCCCC", "No data")],
        "ramp": [(1, "#99D9EA", 1.0, "1 month of water"), (12, "#0000AA", 1.0, "12 months of water (permanent water)")],
    },
    "recurrence": {
        "title": "Water recurrence",
        "band": "recurrence",
        "unit": "percent",
        "kind": "continuous",
        "interval": FULL,
        "summary": "How often water returned from year to year, as a percentage of observation years within each pixel's water period.",
        "guide": (
            "Water recurrence is a measurement of the degree of inter-annual variability in the presence of water. "
            "This describes how frequently water returned from one year to another (expressed as a percentage). "
            "[...] Water recurrence is then calculated as the ratio of the number of water years to observation years."
        ),
        "values": [(0, "#FFFFFF", "Not water"), (255, "#CCCCCC", "No data")],
        "ramp": [(1, "#FF7F27", 1.0, "1% recurrence"), (100, "#99D9EA", 1.0, "100% recurrence")],
    },
    "transitions": {
        "title": "Water transitions",
        "band": "transition",
        "unit": None,
        "kind": "classes",
        "interval": FULL,
        "summary": "Change in seasonality between the first and last year of observation: ten classes of water transition.",
        "guide": (
            "The Transitions map provides information on the change in seasonality between the first and last "
            "years and captures changes between the three classes of not water, seasonal water and permanent water. "
            "[...] These conversions refer to changes in state from the beginning and end of the time series; they "
            "do not describe what happened in the intervening years."
        ),
        "values": [
            (0, "#FFFFFF", "Not water"),
            (1, "#0000FF", "Permanent"),
            (2, "#22B14C", "New permanent"),
            (3, "#D1102D", "Lost permanent"),
            (4, "#99D9EA", "Seasonal"),
            (5, "#B5E61D", "New seasonal"),
            (6, "#E6A1AA", "Lost seasonal"),
            (7, "#FF7F27", "Seasonal to permanent"),
            (8, "#FFC90E", "Permanent to seasonal"),
            (9, "#7F7F7F", "Ephemeral permanent"),
            (10, "#C3C3C3", "Ephemeral seasonal"),
            (255, "#CCCCCC", "No data"),
        ],
        "ramp": None,
    },
    "extent": {
        "title": "Maximum water extent",
        "band": "max_extent",
        "unit": None,
        "kind": "classes",
        "interval": FULL,
        "summary": "Every location ever detected as water, 1984 to 2024.",
        "guide": (
            "The Maximum Water Extent provides information on all the locations ever detected as water over the "
            "41-year period. It is the union of all the other datasets."
        ),
        "values": [(0, "#FFFFFF", "Not water"), (1, "#6666FF", "Water detected"), (255, "#CCCCCC", "No data")],
        "ramp": None,
    },
}

# Overview resampling. Continuous percentages average; coded values take the
# most common class so no invented class appears.
RESAMPLING = {"occurrence": "average", "recurrence": "average", "seasonality": "mode",
              "change": "mode", "transitions": "mode", "extent": "max"}
