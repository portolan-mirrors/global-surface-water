# Global Surface Water Explorer v1.5: Portolan mirror

Build scripts and STAC metadata for the Portolan mirror of the six aggregated
layers of the JRC/Google [Global Surface Water Explorer](https://global-surface-water.appspot.com/)
v1.5 (1984 to 2024): occurrence, occurrence change intensity, seasonality,
recurrence, transitions, and maximum extent.

- Catalog: <https://data.source.coop/portolan-mirrors/global-surface-water/catalog.json>
- Browse: <https://browser.portolan-sdi.org/#/external/data.source.coop/portolan-mirrors/global-surface-water/catalog.json>
- Source Cooperative: <https://source.coop/portolan-mirrors/global-surface-water>
- Request: [portolan-data#82](https://github.com/portolan-sdi/portolan-data/issues/82)

Each layer is a collection of the 504 upstream 10° tiles, copied byte for
byte from the CloudFerro bucket the download page links, plus one global
overview COG at 0.004° for display. Data files live in object storage, never
in git.

## Layout

| Path | What it is |
|---|---|
| `catalog/` | The published catalog. Data files under it are gitignored. |
| `manifest/upstream.json` | Name, size, and hash of every upstream tile at build time. |
| `tools/products.py` | Every per-layer fact (titles, value tables, colours), from the Data Users Guide. |
| `tools/upstream.py` | Lists the upstream bucket; `--diff` and `--new-prefixes` detect changes. |
| `tools/build.sh` | Downloads and checks the tiles (`fetch.py`), builds the overviews (`make_overview.py`). |
| `tools/stac.sh` | Thumbnails, STAC JSON, item index, agent guides, READMEs. |
| `tests/` | Gates CI runs on every PR, plus `test_agent_claims.py` for the guide recipes. |

## Updating from upstream

`.github/workflows/upstream-check.yml` runs weekly. When the CloudFerro
listing differs from `manifest/upstream.json`, or a new prefix appears on the
bucket (a likely new release), it opens an issue titled "Upstream: GSWE tiles
changed on CloudFerro". The rebuild is manual, because it moves about 40 GB.
On a large machine (64 cores, 160 GB RAM, 100 GB disk), from a clone with the
current catalog data in `catalog/`:

```bash
tools/build.sh      # refresh manifest, fetch changed tiles, rebuild overviews
tools/stac.sh       # STAC, thumbnails, guides, READMEs
python3 tests/run_all.py
GUIDE_BASE=$PWD/catalog python3 tests/test_agent_claims.py
eval "$(source-coop creds --format env)"
AWS_ENDPOINT_URL=https://data.source.coop python3 tools/publish.py --confirm
git add -A && git commit -m "chore: sync with upstream" && git push
```

`tools/fetch.py` downloads only tiles that are missing or have a different
size; delete a tile first to force it. A new release under a new prefix
(say `Aggregated/VER1-6/`) needs `PREFIX` in `tools/upstream.py`, the
version strings in `tools/products.py` and `.portolan/metadata.yaml`, and a
new catalog version.

`tools/publish.py` uploads only what differs from the bucket, and never
deletes. Publishing writes `catalog/` (tiles, overviews, and metadata) to
`s3://portolan-mirrors/global-surface-water/`.

## License

The data: see `catalog/.portolan/metadata.yaml` (attribution "Source: EC
JRC/Google"; cite Pekel et al. 2016). The code in this repository: see
`LICENSE`.
