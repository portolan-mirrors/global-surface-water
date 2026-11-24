#!/usr/bin/env bash
# Rebuild the data: list upstream, download every tile, check it against the
# upstream hash, and build the six overview COGs. Then run tools/stac.sh.
#
#   tools/build.sh            # full rebuild (~40 GB download, ~20 min on 64 cores)
#
# Run it on a large machine (see README "Updating from upstream"). Data goes
# under catalog/ (gitignored); scratch goes to ../work.
set -euo pipefail
REPO=$(cd "$(dirname "$0")/.." && pwd)
WORK=${WORK:-$REPO/../work}
cd "$REPO"
mkdir -p "$WORK"

python3 -I tools/upstream.py --write manifest/upstream.json
python3 -I tools/fetch.py manifest/upstream.json catalog "$WORK"
systemd-run --user --scope -q -p MemoryMax=160G \
  python3 -I tools/make_overview.py catalog occurrence change seasonality recurrence transitions extent
