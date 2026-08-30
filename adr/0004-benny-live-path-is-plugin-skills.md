# Live grok Benny path is plugin skills

- Status: accepted, supersedes ADR-0002
- Date: 2026-08-31
- Supersedes: ADR-0002

## Context

ADR-0002 kept Cursor `automations/benny/skills/` as the upstream reference and named `automations/benny/grok/triage.md` as the live contract. That nested live path is gone. Enable pstack now loads `/benny-triage` from `automations/benny-grok/skills/`.

## Decision

Cursor `automations/benny/skills/` remains the upstream reference for marker names and atomic intent. The live grok path is `automations/benny-grok/skills/benny-triage/SKILL.md` and `benny-repro/SKILL.md`, listed in `plugin.json` `skills`. No copy into a target `.grok/` tree.

## Consequences

ADR-0002's live-path sentence is retired. The reference-pack sentence stands. ADR-0003 still forbids a plugin `hooks` key.
