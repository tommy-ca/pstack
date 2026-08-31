## Why

Tag `v0.14.5-grokbuild.3` exists and a GitHub Release exists, but workflow `release.yml` has never run. The Release was created by `gh release create` on a laptop. `tests/test_release.py` only greps files, so it stayed green. Operators cannot trust Actions to publish the next tag.

## What Changes

- `scripts/release.sh` still tags with `grok plugin tag --push` and never `--force`. After the tag is on origin it also converges to a GitHub Release (`gh release view` or `gh release create --verify-tag --generate-notes`).
- `.github/workflows/release.yml` does the same Release step. It still does not call `grok`.
- Nested grok cannot write `.git/refs/tags`. The script refuses `__GROK_INSIDE_BWRAP` and the natives page names host-shell `grok --sandbox off`.
- Tests lock `gh release view`, `gh release create --verify-tag`, no `--force`, no `grok plugin tag` in Actions, no `workflow_dispatch`.
- After this lands on `main`, bump `plugin.json` to `0.14.5-grokbuild.4` and run `scripts/release.sh` so Actions can fire on a tag that is not the first workflow in the repo.
- Catalog pin in `grok-build-plugins` follows the new pstack SHA. Not sibling tags.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `pstack-release-tag`: GitHub Release is idempotent from the local script and from Actions. Local tag still comes only from `grok plugin tag`.

## Impact

`scripts/release.sh`, `.github/workflows/release.yml`, `tests/test_release.py`, `docs/guide/13-grok-natives.md`, `HARNESS.md` sandbox/tag row, `plugin.json` version, then catalog marketplace sha. Not Cursor playbooks. Not leftover OpenSpec changes on main.
