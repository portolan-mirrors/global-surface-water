#!/usr/bin/env python3
"""Download every tile in the manifest into catalog/<layer>/<tile>/<tile>.tif
and check it against the upstream object.

    python3 -I tools/fetch.py manifest/upstream.json catalog WORK

aria2c downloads (16 files at a time). Each file is then checked against the
listing: a plain MD5 hash is compared directly; an S3 multipart ETag
("<md5>-1") is the MD5 of the file's MD5; a multipart ETag with more parts
cannot be recomputed without the part size, so those files are downloaded a
second time and compared byte for byte. A tile already on disk with the
right size is skipped.
"""
import filecmp
import hashlib
import json
import re
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

man = json.loads(Path(sys.argv[1]).read_text())
CAT, WORK = Path(sys.argv[2]).resolve(), Path(sys.argv[3]).resolve()
TILE = re.compile(r"^[a-z]+_(\d+[EW]_\d+[NS])_")


def dest(key):
    layer, fname = key.split("/")
    t = TILE.match(fname)[1]
    return CAT / layer / t / f"{t}.tif"


def aria(pairs, listfile):
    listfile.write_text("".join(f"{man['base']}{k}\n  dir={p.parent}\n  out={p.name}\n" for k, p in pairs))
    subprocess.run(["aria2c", "-i", str(listfile), "-j16", "-x4", "-s4", "--auto-file-renaming=false",
                    "--allow-overwrite=true", "--console-log-level=warn", "--summary-interval=0",
                    "--max-tries=10", "--retry-wait=5"], check=True)


def md5(p, chunk=1 << 24):
    h = hashlib.md5()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(chunk), b""):
            h.update(b)
    return h


def check(item):
    key, v = item
    p = dest(key)
    if p.stat().st_size != v["bytes"]:
        return key, "size"
    tag = v["md5"]
    if "-" not in tag:
        return key, "ok" if md5(p).hexdigest() == tag else "bad"
    if tag.endswith("-1"):
        return key, "ok" if hashlib.md5(md5(p).digest()).hexdigest() + "-1" == tag else "bad"
    return key, "twice"


def main():
    WORK.mkdir(exist_ok=True)
    tiles = man["tiles"]
    todo = [(k, dest(k)) for k, v in tiles.items()
            if not dest(k).exists() or dest(k).stat().st_size != v["bytes"]]
    for _, p in todo:
        p.parent.mkdir(parents=True, exist_ok=True)
    if todo:
        aria(todo, WORK / "aria2.txt")
    with ThreadPoolExecutor(32) as ex:
        res = dict(ex.map(check, tiles.items()))
    twice = [k for k, r in res.items() if r == "twice"]
    if twice:
        again = [(k, WORK / "recheck" / k) for k in twice]
        aria(again, WORK / "recheck.txt")
        for k, p in again:
            res[k] = "ok" if filecmp.cmp(p, dest(k), shallow=False) else "bad"
            p.unlink()
    bad = sorted(k for k, r in res.items() if r != "ok")
    print(f"{len(tiles)} tiles, {len(todo)} downloaded, {len(twice)} compared twice, {len(bad)} bad")
    if bad:
        print("\n".join(bad[:50]))
        sys.exit(1)


main()
