# Port pstack to another host or domain

Official pstack (poteto, Cursor plugin pin `6fecddba`) is a philosophy plus a file layout. This Grok port is a **reference implementation** of that layout on a second host. Use this page to port the core to Claude, Codex, another TUI, or a non-coding domain (ops, research, support).

## Philosophy (keep this)

From the official README and `docs/guide/08-principles.md`:

- **Less code, higher quality.** Throughput without quality is not the goal. Opposite of maximizing loc.
- **Go deep, then parallelize.** Trust each agent because it applies the same principles. Then fan out.
- **One router.** `/poteto-mode` matches a playbook and calls situational skills. The operator gives a goal and a checkable outcome in their own words.
- **Steer with principle names.** 21 principles as leaf skills. You do not invoke them. One phrase redirects. The agent must name the decision the principle changed.
- **Prove on the real artifact.** Compiling is not done.
- **Never block on reversible work.** Pause on irreversible writes.
- **Encode lessons in structure.** The second time you write an instruction, turn it into a check or script. **Laziness Protocol** is the default sizing rule: smallest change, prefer deletion.

Fork it. Improve it. The official README says PRs are welcome. A port that copies files and keeps Cursor `Task` fields is not a port.

## Three layers

| Layer | What | Port how |
|---|---|---|
| Core | 21 `principle-*` skills, 22 playbook **intents**, router skill shape, unslop, no-comments, tdd, how, why | Copy. Keep names. |
| Host map | Spawn primitive, join, overnight loop, skill order vs that host's builtins | Write a new map file. Grok: `HARNESS.md`. Codex: `codex-tools.md`. Claude: `Agent`. |
| Domain packs | Benny, TypeScript practices, visual-parity, Graphite shipping | Keep only if the domain matches. Do not ship Cursor automations as live grok hooks. |

The host map is the only required new file. Playbooks copy their steps verbatim. They call the map's tool names, not Cursor Task fields.

## Recipe

1. Copy `skills/principle-*` and `skills/poteto-mode/` (playbooks + router).
2. Write `<host-map>.md` with spawn, join, effort, skill order, overnight. Point the router's first todo at that file.
3. Register skills and role agents in the host's plugin or skill dirs.
4. Run a scanner that forbids leftover host-A identifiers in playbooks (this repo: `scripts/verify-harness.py`).
5. Skip `make-bot-ui` unless the host has that canvas. Skip Benny until you remap Slack and fail-closed.

This repo already did those steps for Grok Build. `UPSTREAM` names the Cursor pin. `scripts/sync-from-upstream.py` is print-only. `adapt-harness.py` rewrites Cursor call sites.

## What not to copy as "core"

- Cursor panel slugs and `Task` fields.
- Plugin-global merge-deny hooks.
- Rhai clones of playbooks (ADR 0005). Workflows belong in a **target** repo if the host has them.
- A 63-plugin marketplace tree. pstack is one plugin.

Next: [Grok Build workflows](./11-grok-workflows.md) if the host is Grok. Official principles: [Steer with principle names](./08-principles.md).
