## Why

`scripts/release.sh` only refuses `__GROK_INSIDE_BWRAP`. The last cut created a local tag, then `grok plugin tag --push` failed on SSH config ownership with that env unset. Specs and docs still describe a host-shell wrapper around `grok plugin tag --push` without passing `--sandbox off` to grok. Origin never saw the tag until a human `git push`.

## What Changes

- The script calls `grok --sandbox off plugin tag --push`. If a local tag exists and origin does not, it `git push origin` that ref. Still no `--force`.
- Specs add `TagLocalUnpushed` and say dispatcher proof is a successful `on.push.tags` run. GitHub Release author is first writer, not the proof.
- Natives and HARNESS name `--sandbox off` on the grok tag argv. Catalog pin stays `origin/main` after archive, not the tag SHA.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `pstack-release-tag`: host-shell grok tags, git push recovers a local-only tag, dual-writer Release, Actions run is the dispatcher proof.

## Impact

`scripts/release.sh`, `tests/test_release.py`, `docs/guide/13-grok-natives.md`, `HARNESS.md`, live spec `openspec/specs/pstack-release-tag/spec.md`. Not a version bump. Not a retag. Not leftover OpenSpec changes. Not Cursor playbooks.
