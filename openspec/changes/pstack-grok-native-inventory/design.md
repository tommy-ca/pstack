## Context

grok 1.0.13 CLI (`5e9a58528b76`). User-guide 04, 14, 15, 19, 27. PluginManifest has unused `commands`, `hooks`, `mcpServers`, `lspServers`. HARNESS already maps the playbook-critical subset.

## Goals / Non-Goals

**Goals:** Inventory. Adopt/skip/gap. Later optional TEST-PLAN `grok plugin validate`.

**Non-Goals:** Implementing wrappers this change. Plugin hooks. `/goal` as a pstack skill.

## Decisions

1. **Skip `/plan` and `/goal` clones.** Architect and figure-it-out stay pstack.
2. **`grok -p` is a Benny gap fill**, not a playbook.
3. **`grok --worktree` is session-level.** Spawn isolation stays `isolation: worktree`.
4. **No plugin MCP/LSP/hooks.**

## Risks / Trade-offs

- [Inventory rot vs grok bumps] -> Pin `grok --version` on the page.
- [Operators want /goal] -> Skill order already has builtin column 3.

## Migration Plan

Docs only. Optional later TEST-PLAN validate step.

## Open Questions

Whether `grok plugin validate` belongs in `verify-harness.py` or TEST-PLAN only.
