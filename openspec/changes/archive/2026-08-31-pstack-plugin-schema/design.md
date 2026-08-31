## Context

Retrospective artifact for the archived `pstack-plugin-schema` change. The proposal records a Grok 1.0.13 manifest and agent-YAML audit: `displayName` was not parsed, `permissionMode: plan` was unsupported, `background:` was not the spawn field, and pstack did not need commands or other host-extension clones. The design handoff was omitted from the archive.

## Goals / Non-Goals

**Goals:**

- Keep only manifest fields parsed by the target Grok host.
- Keep agent YAML to supported spawn metadata and use `pstack:<role-key>` overlay stems.
- Describe pstack as skills plus agents, without speculative commands, hooks, MCP, or LSP clones.
- Lock the schema facts with repository tests.

**Non-Goals:**

- No plugin index unless `require_sha` is enabled.
- No new host features or compatibility aliases for unsupported fields.
- No change to the source skill inventory.

## Decisions

1. Remove ignored or unsupported manifest/YAML fields rather than documenting them as active behavior.
2. Keep `effort`, `capabilityMode: execute`, and `inheritSkills` because the archived proposal identifies them as supported.
3. Represent setup overlays under `~/.grok/roles/pstack:<key>.toml`.
4. Treat the plugin schema and agent declarations as one tested host boundary.

## Verification

The archived task checklist records the manifest/version update, removal of unsupported fields, HARNESS/setup documentation, and parsed-field tests. This design is reconstructed from those artifacts.
