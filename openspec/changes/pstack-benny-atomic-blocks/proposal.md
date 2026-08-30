## Why

Benny is a Cursor automation pack for Slack issue reports. Two pipelines. One triages. One reproduces confirmed bugs and may open a draft pull request. Official pstack ships it as dormant source under `automations/benny/`. The grok port left it unwired. Grok has no Cursor `/automate` runtime and no Slack channel auto-trigger. We need an intent-driven spec of Benny's atomic blocks so a grok remap uses hooks and workflows without registering the pack as slash skills or installing plugin-global hooks.

## What Changes

- OpenSpec capabilities for pack layout, triage, repro, fail-closed safety, and the grok remap.
- Design doc: Cursor vs grok mapping, data flow, schemas.
- Opt-in grok copies under `automations/benny/grok/` (hooks + workflows). Operators copy them into a target repo. pstack `plugin.json` still has no `hooks` key.

## Capabilities

### New Capabilities

- `benny-pack`: dormant source. Not slash skills. User config lives outside the pack.
- `benny-triage`: one thread-only verdict with `[benny:bug]`, `[benny:performance]`, or `[benny:other]`.
- `benny-repro`: wait for a trusted marker, reproduce twice through real UI, draft PR only after proof.
- `benny-safety`: immutable source coordinates, no source-channel root posts, no worker Slack writes, draft-only PRs.
- `benny-grok-remap`: copy `automations/benny/grok/` into target `.grok/hooks/` and `.grok/workflows/`. Invoke with `/workflow` or `/loop` → `scheduler_create`. No Slack auto-start.

### Modified Capabilities

None.

## Impact

`openspec/changes/pstack-benny-atomic-blocks/`, `docs/superpowers/specs/2026-08-30-pstack-benny-atomic-blocks-design.md`, `automations/benny/grok/`. No plugin-wide hooks. Skip Cursor `/automate` and `control-cli`.
