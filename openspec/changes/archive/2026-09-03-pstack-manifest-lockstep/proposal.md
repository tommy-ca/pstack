## Why

The upstream refresh published pstack as `0.14.7-grokbuild.0`, but the tracked `.agents/plugins/marketplace.json` overlay still declares `0.14.5-grokbuild.3`. That drift weakens the repository's manifest identity contract and can make an agent-plugin consumer resolve stale metadata. A separate change keeps the completed upstream refresh history bounded while repairing the discovered contract gap.

## What Changes

- Define one lockstep version contract for every tracked pstack manifest surface, including `.agents/plugins/marketplace.json`, `plugin.json`, the Grok/Codex/Claude manifests, and the Claude marketplace entry.
- Update `.agents/plugins/marketplace.json` to the current adapter version `0.14.7-grokbuild.0`.
- Extend the existing manifest verification test to parse the tracked manifest set and fail when any version drifts from `plugin.json`.
- Preserve the existing SemVer adapter grammar and single-repository identity rules.
- Do not change runtime host mappings, add dependencies, mutate the sibling marketplace checkout, or perform release/tag/push operations as part of implementation.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `pstack-plugin-schema`: require version consistency across all tracked pstack manifest surfaces and provide a regression scenario for stale overlay metadata.

## Impact

`.agents/plugins/marketplace.json`, `tests/test_verify_harness.py`, and the `pstack-plugin-schema` specification. The existing root and host manifests remain unchanged except where the shared version contract requires them to be compared. No new dependency or runtime service is required.
