## Why

Grok Build workflows are Rhai scripts under `.grok/workflows/` or `~/.grok/workflows/`. They are not a plugin.json field. pstack's live router is `/poteto-mode` plus markdown playbooks. Cloning those 22 playbooks into Rhai would not load with `grok plugin enable pstack`, would skip playbook match, and would not spawn `pstack:<role>` unless each script reinvented that. We need a spec that forbids that clone.

## What Changes

- OpenSpec capability `pstack-playbooks-not-rhai`.
- ADR `0005-playbooks-are-not-rhai-workflows.md`.
- Tests lock no plugin `workflows` key, no repo `.grok/workflows/`, no `playbooks/*.rhai`.

## Capabilities

### New Capabilities

- `pstack-playbooks-not-rhai`: playbooks stay markdown. Plugin does not ship Rhai. Benny `.rhai` files stay optional copies, not the router.

### Modified Capabilities

None.

## Impact

`openspec/changes/pstack-playbooks-not-rhai/`, `adr/0005-playbooks-are-not-rhai-workflows.md`, `tests/test_verify_harness.py`. No playbook rewrite.
