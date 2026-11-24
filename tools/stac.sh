#!/usr/bin/env bash
# Write the STAC, item index, thumbnails, guides, and READMEs; then check.
# Reads no tile pixels except for the thumbnails. Takes about a minute.
set -euo pipefail
REPO=$(cd "$(dirname "$0")/.." && pwd)
cd "$REPO"
uv run -q --python /usr/bin/python3 --with pillow --with "numpy<2" \
  python -I tools/make_thumbs.py catalog "${WORK:-$REPO/../work}"
python3 -I tools/stac.py catalog manifest/upstream.json
(cd catalog && portolan stac-geoparquet)
python3 -I tools/stac.py catalog manifest/upstream.json   # picks up items.parquet
python3 -I tools/agents.py catalog
(cd catalog && portolan readme)
python3 -I tools/fix_readmes.py catalog
