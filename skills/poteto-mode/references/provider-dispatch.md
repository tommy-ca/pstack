# Provider dispatch

Shared pstack blocks recompose on **Grok Build**, **Codex**, and **Claude Code**. The parent owns every route. Children never detect the host or spawn.

## Descriptors

```text
<provider>:<model>@<effort>
```

`inherit-parent` and `auto` omit host `model` so the child uses the parent session.

## Stock routes (no Cursor panel slugs as live fallbacks)

Do not send Cursor marketplace panel slugs as live spawn models unless `/setup-pstack` confirmed they exist on **this** host. Stock Grok Build uses `grok-4.6` and `grok-4.5` only.

| Role | Grok Build | Codex | Claude Code | Antigravity |
| --- | --- | --- | --- | --- |
| Judgment / prose | `grok-4.6` | `gpt-6.1-sol` (judgment), `gpt-6-luna` (prose) | detected Claude slug | `gemini-4-hydrogen-high` (`pro`; `gemini-4-argon-high` on paid Pro subs) |
| Mechanical / fast | `grok-4.5` | `gpt-6-luna` | detected Claude slug | `gemini-3.8-flash-high` (`flash`) |
| Panel seats | unique detected slugs only; never four copies of one slug | `gpt-6.1-sol`, `gpt-6-luna` (astra minimal to hardest tasks) | unique detected slugs only | `gemini-4-hydrogen-high`, `gemini-3.8-flash-high` (`pro, flash`; `claude-opus-5-5-high` minimal to `hardest-tasks`; no `gpt-oss-*`) |

Effort on Grok Build is role overlay (`~/.grok/roles/pstack:<key>.toml`) or agent frontmatter. Do not send `reasoning_effort` on Grok `task`. Codex may pass `reasoning_effort` on `spawn_agent` when that host supports it. Antigravity carries reasoning effort inside the concrete model slug rather than a separate `default effort` or `@<level>` suffix.

## Parent spawn

| Parent | Spawn |
| --- | --- |
| Grok Build | `task` (TUI alias `spawn_subagent`). Depth 1. `isolation: worktree` for writers. |
| Claude Code | `Agent`. Depth 1. Native Claude models stay in-process. |
| Codex | `spawn_agent` / `wait_agent` with `multi_agent = true`. Depth 1. |
| Antigravity | `invoke_subagent` (`pro`, `flash`, `flash_lite`, `inherit`) or `swarm(action="add", model=...)`. Depth 1. |

## Mapping files

- Grok Build: `grok-tools.md`
- Codex: this file plus `codex-tools.md`
- Claude Code: `.claude-plugin/plugin.json` plus Claude `Agent`
- Antigravity: `antigravity-tools.md` plus `.antigravity-plugin/models.json`

Optional external CLI runner under `skills/poteto-mode/scripts/runner/` is for **outbound** other-provider lanes, not for Grok Build as the in-process host.
