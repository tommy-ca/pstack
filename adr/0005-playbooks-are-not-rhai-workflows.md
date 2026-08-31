# Playbooks are not Rhai workflows

- Status: accepted
- Date: 2026-08-31

## Context

Grok workflows are Rhai scripts discovered from `.grok/workflows/` and `~/.grok/workflows/`. They are not a `plugin.json` field. pstack's router is `/poteto-mode`. Cloning 22 playbooks into Rhai would not load on `grok plugin enable pstack`.

## Decision

Keep playbooks as markdown under `skills/poteto-mode/playbooks/`. Do not add a `workflows` key to `plugin.json`. Do not add `.grok/workflows/` playbook clones to this plugin repo. Optional Benny `.rhai` files stay copies. They do not replace `/poteto-mode` or `/benny-triage`.

## Consequences

A bounded fan-out pipeline belongs in a target repository's `.grok/workflows/`, not in this plugin. Enable pstack still loads slash skills and `pstack:<role>` agents only.
