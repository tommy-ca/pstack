## Why

pstack is one plugin in one git repo with a root `plugin.json`. Claude and Codex adapters use `source: "./"`. A later agent could relocate the tree into `grok-build-plugins/pstack` to copy Cursor's sibling farm. That would break `grok plugin install tommy-ca/pstack --trust`, mix a grok catalog with Claude/Codex indexes, and put pstack tags on catalog HEAD.

## What Changes

- Specs say pstack MUST remain `tommy-ca/pstack` with a repo-root `plugin.json`.
- It MUST NOT live as `grok-build-plugins/pstack` or `plugins/pstack`.
- Install stays `tommy-ca/pstack --trust`. No retag. No version bump.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `pstack-release-tag`: one plugin, one git repo. Not a catalog sibling folder.

## Impact

`openspec/specs/pstack-release-tag/spec.md`, ADR 0011, `docs/guide/13-grok-natives.md` or README. Not existing git tags. Not a catalog file move.
