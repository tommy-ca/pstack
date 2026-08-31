## Why

grok 1.0.13 `PluginManifest` has 14 parsed fields. `displayName` is ignored. `permissionMode: plan` is not in `PermissionMode`. Agent YAML `background:` is not the spawn field. Docs listed `commands/` as if pstack needed them.

## What Changes

- Drop `displayName`. Bump version to `0.14.5-grokbuild.3`.
- Drop `permissionMode: plan` and agent `background: true`. Keep `effort`, `capabilityMode: execute`, `inheritSkills`. Overlay stems `~/.grok/roles/pstack:<key>.toml`.
- HARNESS **Plugin schema** plus 01-setup: skills+agents only, no commands/hooks/MCP/LSP clones.
- Tests lock those facts. No `plugin-index.json` unless require_sha is on.

## Capabilities

### New Capabilities

- `pstack-plugin-schema`: grok 1.0.13 manifest and agent YAML contract.

### Modified Capabilities

None.

## Impact

- `plugin.json`, `agents/*.md`, `HARNESS.md`, `docs/guide/01-setup.md`, `tests/test_verify_harness.py`.
