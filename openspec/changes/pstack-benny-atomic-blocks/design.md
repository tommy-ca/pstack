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

1. **Plugin skills, not plugin hooks.** Live grok Benny is `automations/benny-grok/` and `plugin.json` `skills` includes that tree. Enable pstack loads `/benny-triage`. Alternative was `plugin.json` `hooks`. Rejected because trusted plugin hooks run in every pstack session.

2. **Hook only merge and force-push.** `fail-closed.sh` denies `gh pr merge`, `git push --force` / `-f`, and `gt merge`. Slack freeze and worker isolation stay prompt-enforced in grok `triage.md` / `repro.md`. Alternative was a PreToolUse matcher on Slack MCP names. Rejected. We do not know the live `server__tool` id, and fail-open on crash would still post.

3. **Workflows take `args.thread_url`.** Rhai reserves `thread`. Isolation worktrees are off for repro so a draft PR can land in the parent tree. Freeze source coordinates from that permalink.

4. **Ship the intent-driven schema in-tree.** Copy `openspec/schemas/intent-driven/` from the same definition the OpenSpec skills describe. Alternative was flipping `config.yaml` to `spec-driven`. Rejected. Every pstack change already declares `schema: intent-driven`.

5. **Cursor SKILL.md is upstream reference.** Live grok contract is `automations/benny-grok/skills/benny-triage/SKILL.md` and `benny-repro/SKILL.md`. Marker names and atomic intent stay shared with the reference pack.

## Risks / Trade-offs

- [Prompt-only Slack policy] -> Agents can still post a root message if they ignore grok `triage.md`. Mitigation is coordinator-only writes in that file, plus no Slack credentials on children. Not a hook.
- [Hooks fail open on crash] -> Deny JSON must print. Tests drive `fail-closed.sh` with real stdin.
- [No Slack auto-start] -> Document `args.thread_url` and external `grok -p`. Do not fake a subscription.
- [Schema copy drift vs dev-env] -> Lock `openspec status --change pstack-benny-atomic-blocks` in tests so a missing schema fails CI.

## Migration Plan

Enable pstack. Type `/benny-triage`. No copy. Rollback is disable pstack or remove the skills path. `plugin.json` never gained `hooks`.

## Open Questions

- Which Slack MCP `server__tool` name this operator will actually run.
- Whether a later change should add a project-local PreToolUse matcher once that name is known.
