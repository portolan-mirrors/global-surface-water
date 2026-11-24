#!/usr/bin/env python3
"""List the GSWE v1.5 aggregated tiles on CloudFerro Swift and write or diff a manifest.

Usage:
  upstream.py --write manifest/upstream.json
  upstream.py --diff  manifest/upstream.json   # exit 1 and print a markdown report on change
  upstream.py --new-prefixes                   # exit 1 if the bucket has prefixes not seen at build time

The bucket is OpenStack Swift; its JSON listing gives name, bytes, hash, and
last_modified per object. `hash` is an MD5, or an S3 multipart ETag
("<md5>-<parts>") for objects uploaded in parts.
"""
import argparse, json, re, sys, urllib.parse, urllib.request

BASE = "https://s3.waw4-1.cloudferro.com/swift/v1/global-surface-water/"
PREFIX = "download2024/Aggregated/VER1-5/"
PRODUCTS = ["change", "extent", "occurrence", "recurrence", "seasonality", "transitions"]
# Keep only the canonical naming; occurrence also has *_p41_Occurrence.tif duplicates.
NAME = re.compile(r"^(?P<p>[a-z]+)_(?P<lon>\d+[EW])_(?P<lat>\d+[NS])_v1_5_2024\.tif$")


def listing():
    out, marker = [], ""
    while True:
        q = urllib.parse.urlencode({"format": "json", "prefix": PREFIX, "limit": 10000, "marker": marker})
        with urllib.request.urlopen(f"{BASE}?{q}", timeout=120) as r:
            page = json.load(r)
        if not page:
            return out
        out += page
        marker = page[-1]["name"]


# Prefixes present when the mirror was built (2026-11-24). A new release is
# expected to appear as a new one, such as download2025/ or Aggregated/VER1-6/.
KNOWN = {
    "": {"MonthlyHistory/", "download2024/", "nohup.out"},
    "download2024/": {"download2024/", "download2024/Aggregated/", "download2024/monthlyhistory/"},
    "download2024/Aggregated/": {"download2024/Aggregated/", "download2024/Aggregated/VER1-5/"},
}


def prefixes(pre):
    q = urllib.parse.urlencode({"format": "json", "delimiter": "/", "prefix": pre})
    with urllib.request.urlopen(f"{BASE}?{q}", timeout=120) as r:
        return {d.get("subdir", d.get("name")) for d in json.load(r)}


def new_prefixes():
    new = sorted(p for pre, known in KNOWN.items() for p in prefixes(pre) - known)
    if not new:
        print("No new prefixes on the bucket.")
        return
    print("### New prefixes on the bucket\n")
    print("A new prefix may be a new release. Check the download page before rebuilding.\n")
    print("\n".join(f"- `{p}`" for p in new))
    sys.exit(1)


def manifest():
    tiles = {}
    for o in listing():
        rel = o["name"][len(PREFIX):]
        product, _, fname = rel.partition("/")
        m = NAME.match(fname)
        if product in PRODUCTS and m and m["p"] == product:
            tiles[rel] = {"bytes": o["bytes"], "md5": o["hash"], "last_modified": o["last_modified"]}
    return {"base": BASE + PREFIX, "tiles": dict(sorted(tiles.items()))}


def main():
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--write")
    g.add_argument("--diff")
    g.add_argument("--new-prefixes", action="store_true")
    a = ap.parse_args()
    if a.new_prefixes:
        return new_prefixes()
    new = manifest()
    if a.write:
        with open(a.write, "w") as f:
            json.dump(new, f, indent=1)
            f.write("\n")
        n = {p: sum(k.startswith(p + "/") for k in new["tiles"]) for p in PRODUCTS}
        print(json.dumps(n), sum(t["bytes"] for t in new["tiles"].values()) / 1e9, "GB")
        return
    old = json.load(open(a.diff))["tiles"]
    cur = new["tiles"]
    added = sorted(cur.keys() - old.keys())
    removed = sorted(old.keys() - cur.keys())
    changed = sorted(k for k in cur.keys() & old.keys() if cur[k]["md5"] != old[k]["md5"] or cur[k]["bytes"] != old[k]["bytes"])
    if not (added or removed or changed):
        print("No upstream change.")
        return
    print(f"Upstream {BASE}{PREFIX} differs from the committed manifest.\n")
    for label, keys in (("Added", added), ("Changed", changed), ("Removed", removed)):
        if keys:
            print(f"### {label} ({len(keys)})\n")
            print("\n".join(f"- `{k}`" for k in keys[:200]))
            if len(keys) > 200:
                print(f"- … and {len(keys) - 200} more")
            print()
    print("Rebuild on EC2: see README, \"Updating from upstream\".")
    sys.exit(1)


if __name__ == "__main__":
    main()
