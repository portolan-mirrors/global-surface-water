"""Value -> RGBA colormap per product, from the Data Users Guide colours.

Used for the default render (tools/stac.py), the overview colour tables
(tools/make_overview.py), and the thumbnails (tools/make_thumbs.py).
"""
from products import PRODUCTS

# Values drawn transparent so the basemap shows: nodata, and "not water"
# (the guide paints it white, which would hide the basemap).
CLEAR = {"occurrence": {0, 255}, "change": {253, 255}, "seasonality": {0, 255},
         "recurrence": {0, 255}, "transitions": {0, 255}, "extent": {0, 255}}


def rgb(h):
    h = h.lstrip("#")
    return [int(h[i:i + 2], 16) for i in (0, 2, 4)]


def colormap(key):
    """Value -> RGBA for every value the guide defines. Ramps are interpolated
    linearly between the guide's end points; ramp opacity is applied as given
    (occurrence runs from 1% to 100% opacity in the guide)."""
    p = PRODUCTS[key]
    cm = {}
    for v, c, _ in p["values"]:
        cm[v] = rgb(c) + [0 if v in CLEAR[key] else 255]
    ramp = p["ramp"] or []
    for (v0, c0, a0, _), (v1, c1, a1, _) in zip(ramp, ramp[1:]):
        for v in range(v0, v1 + 1):
            t = (v - v0) / (v1 - v0)
            col = [round(a + (b - a) * t) for a, b in zip(rgb(c0), rgb(c1))]
            alpha = a0 + (a1 - a0) * t
            # Floor the opacity at 35% so 1-10% occurrence stays visible on a map.
            cm[v] = col + [round(255 * max(alpha, 0.35))]
    return {str(k): cm[k] for k in sorted(cm)}


