# pstack-plugin-schema Specification

## Purpose
TBD - created by archiving change pstack-plugin-schema. Update Purpose after archive.

## Requirements

### Requirement: Manifest uses only deserialized plugin.json keys

Feature: pstack-plugin-schema

`plugin.json` MUST NOT contain `displayName`. `repository` MUST be a string. `author` MUST be an object. The plugin MUST NOT ship `commands/`, `hooks/`, `.mcp.json`, or `.lsp.json`.

#### Scenario: validate extra keys stay out

- **GIVEN** repo-root `plugin.json`
- **WHEN** tests read it
- **THEN** `displayName` is absent
- **AND** `commands/` does not exist

### Requirement: Plugin agents omit invalid permissionMode and YAML background

Feature: pstack-plugin-schema

Agent frontmatter MUST NOT set `permissionMode: plan` or `permissionMode: bypassPermissions`. It MUST NOT set `background:`. Overlay paths MUST use `~/.grok/roles/pstack:<key>.toml`. Spawn background remains `spawn_subagent` `background`.

#### Scenario: how-explorer YAML

- **GIVEN** `agents/how-explorer.md`
- **WHEN** frontmatter is read
- **THEN** it has `effort` and `capabilityMode: execute`
- **AND** it has no `permissionMode: plan`
- **AND** it has no `background: true`
