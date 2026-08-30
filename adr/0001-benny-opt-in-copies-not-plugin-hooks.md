# Benny grok remaps are opt-in copies, not plugin hooks

- Status: accepted
- Date: 2026-08-30

## Context

Trusted pstack plugin hooks run in every session that loads the plugin. Benny is a Slack intake pack for a target product repo. Shipping its fail-closed hook inside pstack `plugin.json` would deny `gh pr merge` for users who never copied Benny.

## Decision

Keep Benny grok remaps under `automations/benny/grok/`. Operators copy hooks and workflows into the target repository. `plugin.json` does not grow a `hooks` key.

## Consequences

Future Benny or automation ports follow the same split. Prompt policy stays in SKILL.md. Merge/force-push deny lives only in the copied hook. Slack auto-start remains a host gap.
