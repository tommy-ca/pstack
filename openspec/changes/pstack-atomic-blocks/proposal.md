## Why

Official Cursor pstack (tree `6fecddba`) is a stack of **atomic building blocks**: a sticky `/poteto-mode` router, 22 playbooks plus `opening-a-pr`, 21 principles, situational skills, two plugin agents, setup overlays, and Cursor harness calls (`Task`, `AskQuestion`, same-run `/loop`). The grok port keeps the first four layers and remaps only the harness. We need an intent-driven spec of those blocks, data flows, and schemas so a Cursor refresh and a grok review share one vocabulary.

## What Changes

- OpenSpec capabilities for router, playbooks, principles, harness map, setup overlays.
- Design doc: data flow and schemas (UPSTREAM pin, `pstack-models.toml`, `~/.grok/roles/pstack:<key>.toml`, `spawn_subagent`).
- Review of this port vs each block (keep / remap / skip).

## Capabilities

### New Capabilities

- `pstack-router`: `/poteto-mode` matches a playbook and copies steps verbatim.
- `pstack-playbooks`: 22 named playbooks plus `opening-a-pr.md`.
- `pstack-principles`: 21 `principle-*` skills, indexed in poteto-mode.
- `pstack-harness-map`: Cursor `Task` → grok `spawn_subagent`; `/loop` → `scheduler_create`.
- `pstack-setup-overlays`: optional `/setup-pstack` writes grok toml + `pstack:<key>` role files.

### Modified Capabilities

None.

## Impact

`openspec/changes/pstack-atomic-blocks/`, `docs/superpowers/specs/2026-08-30-pstack-atomic-blocks-design.md`. No runtime copy of Cursor `make-bot-ui`. Benny stays source-only.
