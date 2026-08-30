## Context

Benny is two Slack pipelines (triage, then gated UI repro) shipped as dormant Cursor automation source under `automations/benny/`. This port left it unwired. `openspec/config.yaml` already named `schema: intent-driven`, but OpenSpec 1.11.0 only ships `spec-driven`, so `openspec status` and `validate` failed until the schema lived at `openspec/schemas/intent-driven/`.

No files exist under `adr/` yet. Nothing in force constrains this design.

## Goals / Non-Goals

**Goals:**
- Specify Benny as atomic blocks (pack, triage, repro, safety, grok remap).
- Remap onto grok natives without registering slash skills or plugin-global hooks.
- Make intent-driven OpenSpec runnable in this repo (`proposal -> specs -> design -> adr -> tasks`).
- Split prompt-enforced Slack rules from hook-enforced merge/force-push.

**Non-Goals:**
- Slack channel auto-start inside grok.
- A first-party Slack MCP in this plugin.
- `control-cli` as the UI adapter.
- Installing Benny SKILL.md files under plugin `skills/`.

## Decisions

1. **Opt-in copies, not plugin hooks.** Put grok files under `automations/benny/grok/`. The operator copies them into a target `.grok/hooks/` and `.grok/workflows/`. Alternative was `plugin.json` `hooks`. Rejected because trusted plugin hooks run in every pstack session.

2. **Hook only merge and force-push.** `fail-closed.sh` denies `gh pr merge`, `git push --force` / `-f`, and `gt merge`. Slack `thread_ts` and worker isolation stay prompt-enforced in SKILL.md and workflow prompts. Alternative was a PreToolUse matcher on Slack MCP names. Rejected. We do not know the live `server__tool` id, and fail-open on crash would still post.

3. **Workflows take `args.thread_url`.** Rhai reserves `thread`. Isolation worktrees are off for repro so a draft PR can land in the parent tree.

4. **Ship the intent-driven schema in-tree.** Copy `openspec/schemas/intent-driven/` from the same definition the OpenSpec skills describe. Alternative was flipping `config.yaml` to `spec-driven`. Rejected. Every pstack change already declares `schema: intent-driven`.

## Risks / Trade-offs

- [Prompt-only Slack policy] -> Agents can still post a root message if they ignore SKILL.md. Mitigation is coordinator-only writes in the prompt, plus no Slack credentials on children. Not a hook.
- [Hooks fail open on crash] -> Deny JSON must print. Tests drive `fail-closed.sh` with real stdin.
- [No Slack auto-start] -> Document `args.thread_url` and external `grok -p`. Do not fake a subscription.
- [Schema copy drift vs dev-env] -> Lock `openspec status --change pstack-benny-atomic-blocks` in tests so a missing schema fails CI.

## Migration Plan

Operators copy `automations/benny/grok/` as in that README. Trust the target folder. Enable pstack from a host shell. No plugin reinstall is required for the schema. Rollback is delete the copied target files. pstack `plugin.json` never gained `hooks`.

## Open Questions

- Which Slack MCP `server__tool` name this operator will actually run.
- Whether a later change should add a project-local PreToolUse matcher once that name is known.
