<!-- ops-sync:begin — synced from portolan-sdi/portolan-ops. Edit there, not here. -->
# Portolan agent norms

All agents MUST read this document before starting work, with no exceptions, ever. (Claude Code does not read `AGENTS.md` but imports this file via a one-line `CLAUDE.md`.) Most of this content is synced downstream from `portolan-ops`. Put repo-specific instructions in `AGENTS.md`, never in `CLAUDE.md`, which the sync overwrites.

## Ground rules

Agents MUST read the complete contents of [norms](https://github.com/portolan-sdi/portolan-ops/blob/main/norms) and [policies](https://github.com/portolan-sdi/portolan-ops/blob/main/policies/) before starting work, with no exceptions, ever.

The [portolan-spec](https://github.com/portolan-sdi/portolan-spec) repo is the absolute ground truth for the Portolan spec. All other tools are downstream of it.

Before documenting any command, flag, or API, verify that it exists.

Use conventional commits always.

All tickets and PRs MUST follow the [templates](https://github.com/portolan-sdi/portolan-ops/blob/main/templates/).

GitHub applies issue forms only in the web UI. With `gh issue create`, write each form field as a `### <field label>` heading, in the form's order. Include `### Priority` with one of `P0` to `P3` from the [priority rubric](https://github.com/portolan-sdi/portolan-ops/blob/main/norms/repos.md#priority). Pass the form's type label with `--label`, and pass the body with `--body-file`. The writing hook denies a body that skips its form, and issue governance flags one.

## Org-wide facts

The canonical homepage is <https://www.portolan-sdi.org/>. Canonical URLs live in [copy/urls.md](https://github.com/portolan-sdi/portolan-ops/blob/main/copy/urls.md). Do not hardcode variants.

Community discussion happens in the [Portolan Google Group](https://groups.google.com/g/portolan) and the [Portolan channel](https://cloudnativegeo.slack.com/archives/C0A1JBH9529) in Cloud-Native Geo Slack. Planning happens in [org-level GitHub projects](https://github.com/orgs/portolan-sdi/projects/1).

Files between `ops-sync` markers are synced from [portolan-ops](https://github.com/portolan-sdi/portolan-ops). They are overwritten on every sync run. To change one, edit it in portolan-ops.

One canonical home per fact. If a value like a color, URL, or policy line exists in portolan-ops, link to it rather than copying it.
<!-- ops-sync:end -->
## This Repository

The build scripts and STAC metadata of the Portolan mirror of the JRC Global
Surface Water Explorer v1.5 aggregated layers. The published catalog is
`https://data.source.coop/portolan-mirrors/global-surface-water/catalog.json`.

### Edit the sources, not the outputs

Every per-layer fact lives in `tools/products.py`, copied from the Data Users
Guide. `tools/stac.py` writes the STAC JSON and the collection
`metadata.yaml` files; `tools/agents.py` writes every `AGENTS.md` under
`catalog/`; `portolan readme` writes every `README.md`. Edit the generator or
the root `catalog/.portolan/metadata.yaml`, then run `tools/stac.sh`. Never
run `portolan add`: it would hash 40 GB and overwrite fields `stac.py` sets.

### The tiles are upstream bytes

Never rewrite a tile. The catalog states that each tile is byte-identical to
the upstream object, and `tools/fetch.py` checks that against
`manifest/upstream.json`. The overviews are the only derived files.

### Checksums

`file:checksum` is a SHOULD and costs a pass over 40 GB, so the tiles and
overviews carry `file:size` only. Do not add a hashing step.

### Validation before publishing

Run `python3 tests/run_all.py`, the local recipe check
(`GUIDE_BASE=$PWD/catalog python3 tests/test_agent_claims.py`), and the
catalog grader on the local catalog. Do not run `portolan check` with the
default data scope: it reads every tile.

### Data never enters git

`.gitignore` excludes every data format. Do not commit a COG or a Parquet file.

### Published agent guides

Every claim in a `catalog/**/AGENTS.md` is quoted from the Data Users Guide
or checked by a fence that `tests/test_agent_claims.py` runs. A fence's
comment lines are its expected output.
