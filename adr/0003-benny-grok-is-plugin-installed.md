# Live grok Benny is plugin-installed

- Status: accepted, supersedes ADR-0001
- Date: 2026-08-30
- Supersedes: ADR-0001

## Context

ADR-0001 kept grok Benny under `automations/benny/grok/` and required a manual copy so a merge-deny hook would not run for every trusted pstack user. That copy is friction. Grok plugins load `skills` from `plugin.json`. They do not load workflows. They do load `hooks` for every trusted user.

## Decision

Live grok Benny lives at `automations/benny-grok/`, a sibling of the Cursor pack. `plugin.json` `skills` includes `./automations/benny-grok/skills/` so `/benny-triage` and `/benny-repro` load after `grok plugin enable pstack`. `plugin.json` still has no `hooks` key. The merge-deny script stays optional and local.

## Consequences

Install is enable pstack. No copy recipe. Nested `automations/benny/grok/` is gone. Cursor `automations/benny/skills/` stays the upstream reference (ADR-0002). Operators who want a local merge-deny hook copy `bin/fail-closed.sh` themselves.
