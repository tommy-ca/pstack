# ADR 0013: Google Antigravity (antigravity-cli / agy) Harness Architecture & Native Plugin Projection

## Context

Following Batch 1 portability (Grok Build, Codex, OMP, OpenCode), pstack is extending support to Google Antigravity (`antigravity-cli` / `agy`). Antigravity is an AI-first platform supporting progressive skill discovery, declarative plugins (`plugin.json`), lifecycle hooks (`hooks.json`), model mappings (`models.json`), subagent declarations (`agents/*.md`), and slash commands (`commands/*.toml`).

We ran an Arena evaluation across 3 architectural candidates to determine how pstack integrates with Antigravity:

- **Candidate 1 (Declarative Native Plugin with Projection Lever):** Single canonical package descriptor (`pstack.package.json`) projecting deterministically into an Antigravity plugin structure (`.antigravity-plugin/plugin.json`, `models.json`, `commands/`, `agents/`).
- **Candidate 2 (Monolithic System Prompt Injection):** Inlining pstack principles and skills into `.gemini/GEMINI.md` or global system instructions without plugin encapsulation.
- **Candidate 3 (Dual Workspace/Global Unmanaged Manifests):** Manually maintaining separate workspace `.agents/` and global `~/.gemini/config/plugins/pstack/` directories without a central projection lever.

## Evaluation & Interrogate Review

- **Candidate 2** was rejected: Inlining 23 principles and playbooks directly into `GEMINI.md` violates Guard the Context Window, wastes token budget, and loses Antigravity's native progressive skill disclosure, subagents, and slash commands.
- **Candidate 3** was rejected: Unmanaged manual copies inevitably drift across versions, violating Build the Lever and Zero Drift.
- **Candidate 1** was selected: Conforms strictly to Antigravity's Customization System. Native plugin manifest `plugin.json` declares skill paths; `models.json` binds pstack roles (`feature`, `bug-fix`, `arena`, `swarm`, `interrogate`) to Antigravity model tiers (`pro`, `flash`, `inherit`); `commands/` declare slash commands; and `agents/` declare native subagents (`poteto-agent.md`, `comment-sicko.md`).

## Decision

1. Add `"antigravity"` to `host_targets` in `pstack.package.json`.
2. Extend `scripts/project-package.py` to project `.antigravity-plugin/plugin.json` and `.antigravity-plugin/models.json`.
3. Map pstack roles to Antigravity model tiers:
   - `feature`: `pro`
   - `bug-fix`: `pro`
   - `interrogate`: `pro`
   - `arena`: `["pro", "flash"]`
   - `swarm`: `flash`
   - default: `inherit`
4. Reconcile the live installation at `~/.gemini/config/plugins/pstack/` from the projected canonical assets.

## Status

Accepted.
