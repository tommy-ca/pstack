## Why

Operators need a grok-native how-to for Rhai workflows, cited from grok-build source. PluginManifest cannot ship them. `/poteto-mode` stays the playbook router. A target repo MAY call `agent_type` `pstack:<role>` from Rhai after enable.

## What Changes

- Guide `docs/guide/11-grok-workflows.md`.
- HARNESS discovery sentence from `WorkflowRegistry::scan`.
- Spec `pstack-grok-workflows`.
- Tests lock the guide and `agent_type`.

## Capabilities

### New Capabilities

- `pstack-grok-workflows`: how to run `/workflow` with pstack roles. No plugin-shipped Rhai. No playbook clones.

### Modified Capabilities

None. ADR 0005 stays in force.

## Impact

`docs/guide/11-grok-workflows.md`, `HARNESS.md`, `openspec/changes/pstack-grok-workflows-howto/`.
