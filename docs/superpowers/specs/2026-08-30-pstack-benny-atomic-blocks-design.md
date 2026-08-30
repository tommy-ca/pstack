# Benny atomic blocks and grok mapping

Date: 2026-08-30
Official pin: `6fecddba65801f9b9c08b8b328d998ee5b09d290` (`UPSTREAM`)
Port: tommy-ca/pstack
Source pack: `automations/benny/`

## Data flow

```
Slack top-level report (Cursor trigger) or args.thread_url (grok)
  -> freeze SOURCE_CHANNEL_ID + SOURCE_THREAD_TS
  -> triage: read thread, how/why cause pass, classify, tracker dedupe
  -> one reply under frozen thread_ts with [benny:bug|performance|other]
  -> repro waits for trusted marker
  -> control adapter drives real UI twice
  -> optional draft PR after before-and-after proof
```

Grok has no Slack channel auto-start. The operator passes `args.thread_url` into `/workflow benny-triage` or `/workflow benny-repro`. Overnight waits use `/loop` → `scheduler_create`. Watch predicates use `monitor`.

## Schemas

**Config** (user-owned, outside the pack). Start from `templates/configuration.example.yaml`. Copy to `.grok/benny/configuration.yaml` on grok, or `.cursor/benny/` on Cursor.

**Markers**

```text
[benny:bug]
[benny:bug] tracker=https://tracker.example/issue/123
[benny:performance]
[benny:performance] tracker=https://tracker.example/issue/123
[benny:other]
```

**Coordinates.** `SOURCE_CHANNEL_ID`, `SOURCE_THREAD_TS`. Optional `OPERATIONS_CHANNEL_ID` / `OPERATIONS_THREAD_TS` never replace source.

**Grok copies.** `automations/benny/grok/hooks/hooks.json` → target `.grok/hooks/`. `automations/benny/grok/workflows/*.rhai` → target `.grok/workflows/`.

## Building blocks vs this port

| Block | Official Cursor | Grok port |
|---|---|---|
| Pack layout | `.cursor/automations/benny/` in the target | `automations/benny/` in pstack. Copy grok extras from `automations/benny/grok/` |
| Slash skills | not registered | not registered. `plugin.json` `skills` stays `./skills/` |
| Setup | point Cursor at `FOR_AGENTS.md`, `/automate` | copy grok files. Enable pstack with `grok plugin enable pstack` |
| User config | `.cursor/benny/` | `.grok/benny/` |
| Slack auto-start | Cursor automations | host gap. Pass `args.thread_url` |
| Triage / repro intent | `skills/*/SKILL.md` **upstream reference** | live grok `grok/triage.md` and `grok/repro.md` |
| Fail-closed merge | prompt only | copied `PreToolUse` hook denies `gh pr merge` and `git push --force` |
| control-cli | Cursor team kit | skip. Drive the real app. Fail closed if the adapter is missing |
| Plugin hooks | n/a | **not** in pstack `plugin.json`. Opt-in target copy only |

## Review of current implementation

**Keep.** Operational SKILL.md files, marker contract, immutable coordinates, draft-only PRs, worker Slack ban.

**Remap.** Cursor `/automate` → grok `/workflow` plus `/loop` → `scheduler_create`. Cursor Slack actions → configured MCP. `.cursor/settings.json` pstack enable → `[plugins].enabled`.

**Skip.** Plugin-global `hooks/`. Slack auto-start. `control-cli`. Registering Benny as slash skills.

**Gaps (host limits).** Grok workflows cannot subscribe to a Slack channel. Depth 1 means the parent fans out workers. Hooks fail open on crash, so deny must be explicit JSON.
