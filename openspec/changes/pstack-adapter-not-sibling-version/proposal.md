## Why

pstack is one plugin in one git repo. The live string `0.14.5-grokbuild.4` is Cursor overlay `0.14.5` plus a grok-build adapter counter. Catalog siblings need the plugin name in the version because they share one tag namespace. Specs name the pstack grammar in isolation. A later agent could "unify" with grok-build-plugins by renaming to `0.14.5-pstack.N` and drop the adapter identity.

## What Changes

- Specs say pstack MUST remain `MAJOR.MINOR.PATCH-grokbuild.N`.
- They MUST NOT copy catalog `MAJOR.MINOR.PATCH-<plugin-name>.N`, including `-pstack.N`.
- Tests reject a `-pstack.N` suffix. No retag. No version bump.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `pstack-release-tag`: adapter identity is grokbuild, not a catalog-style plugin-name prerelease.

## Impact

`openspec/specs/pstack-release-tag/spec.md`, `tests/test_release.py`, `docs/guide/13-grok-natives.md`, ADR 0010. Not existing git tags. Not grok-build-plugins sibling versions.
