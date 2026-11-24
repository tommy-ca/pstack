# Provider dispatch

Shared pstack blocks recompose on **Grok Build**, **Codex**, **Claude Code**, and **Antigravity**. The parent owns every route. Children never detect the host or spawn.

## Descriptors

```text
<provider>:<model>@<effort>
```

`inherit-parent` and `auto` omit host `model` so the child uses the parent session.

## Stock routes (no Cursor panel slugs as live fallbacks)

Do not send Cursor marketplace panel slugs as live spawn models unless `/setup-pstack` confirmed they exist on **this** host. Stock Grok Build uses `grok-4.6` and `grok-4.5` only.

| Role | Grok Build | Codex | Claude Code | Antigravity |
| --- | --- | --- | --- | --- |
| Judgment / prose | `grok-4.6` | `gpt-6.1-sol` (judgment), `gpt-6-luna` (prose) | detected Claude slug | `gemini-4-hydrogen-high` (`pro`; `gemini-4-neon-high` or retiring `gemini-4-argon-high` when available) |
| Mechanical / fast | `grok-4.5` | `gpt-6-luna` | detected Claude slug | `gemini-3.8-flash-high` (`flash`; migrates to `gemini-4-hydrogen-low` after `2026-11-30`) |
| Panel seats | unique detected slugs only; never four copies of one slug | `gpt-6.1-sol`, `gpt-6-luna` (astra minimal to hardest tasks) | unique detected slugs only | `gemini-4-hydrogen-high`, `gemini-3.8-flash-high` (`pro, flash`; optional `claude-opus-4-6-thinking` or `claude-sonnet-4-6`, migrating to `claude-opus-5-5-high` before `2026-11-30`; zero `gpt-oss-*`) |

Effort on Grok Build is role overlay (`~/.grok/roles/pstack:<key>.toml`) or agent frontmatter. Do not send `reasoning_effort` on Grok `task`. Codex may pass `reasoning_effort` on `spawn_agent` when that host supports it. Antigravity forbids `reasoning_effort` on `invoke_subagent` (`setup.effort = "none"`), encoding per-role effort in concrete slugs while supporting CLI `--effort` and TUI `/effort` (`low`, `medium`, `high`, `xhigh`, `max`) for adjustable models (`Orchestrator` excludes effort adjustment).

## Parent spawn

| Parent | Spawn |
| --- | --- |
| Grok Build | `task` (TUI alias `spawn_subagent`). Depth 1. `isolation: worktree` for writers. |
| Claude Code | `Agent`. Depth 1. Native Claude models stay in-process. |
| Codex | `spawn_agent` / `wait_agent` with `multi_agent = true`. Depth 1. |
| Antigravity | `invoke_subagent` (`pro`, `flash`, `flash_lite`, `inherit`), `run_workflow` (`parallel()`, `pipeline()`), or native `swarm` when `/swarm` is active (`swarm_pane`, `swarm_monitor`). Policy depth 1 (runtime limit 10). Gate human choices with `ask_question`. |

## Mapping files

- Grok Build uses `grok-tools.md`.
- Codex uses this file plus `codex-tools.md`.
- Claude Code uses `.claude-plugin/plugin.json` plus Claude `Agent`.
- Antigravity uses `antigravity-tools.md` plus `.antigravity-plugin/models.json`, validated via `agy plugin validate --strict --json` and editor-bridged via `agy acp`.

Optional external CLI runner under `skills/poteto-mode/scripts/runner/` is for **outbound** other-provider lanes, not for Grok Build as the in-process host.
