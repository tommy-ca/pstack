## Why

`grok plugin tag` names the tag `v` plus `plugin.json` version. The live string `0.14.5-grokbuild.4` is SemVer 2.0 with an adapter prerelease. Specs never say that, so a later agent could “fix” it with CalVer or a ship date and drop the Cursor `0.14.5` foreign key.

## What Changes

- Specs name SemVer 2.0: `MAJOR.MINOR.PATCH-grokbuild.N`.
- Calendar versioning and date-only uniqueness are forbidden as the tag identity. Ship day stays in GitHub Release notes.
- Tests lock the version regex. No retag. No version bump.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `pstack-release-tag`: version grammar is SemVer plus grokbuild adapter counter, not CalVer.

## Impact

`openspec/specs/pstack-release-tag/spec.md`, `tests/test_release.py`, `docs/guide/13-grok-natives.md`, ADR 0009. Not existing git tags.
