## Why

`grok plugin tag` is unused. 13-grok-natives still says it waits. There is no GitHub tag or release. Operators cannot `grok plugin install tommy-ca/pstack@v0.14.5-grokbuild.3`.

## What Changes

- Local `scripts/release.sh` runs validate, then `grok plugin tag --push`. No `--force`.
- `.github/workflows/release.yml` on `v*` runs a file-only test and `gh release create`. It does not run `grok` (the runner has no grok).
- Docs stop saying tag waits.

## Capabilities

### New Capabilities

- `pstack-release-tag`: pstack releases are `v{plugin.json version}` via `grok plugin tag`. GitHub Release is created from that tag.

### Modified Capabilities

None.

## Impact

`scripts/release.sh`, `.github/workflows/release.yml`, `docs/guide/13-grok-natives.md`, `tests/test_release.py`. Not the catalog. Not sibling plugins.
