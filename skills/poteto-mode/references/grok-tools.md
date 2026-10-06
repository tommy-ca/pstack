# Grok Build tool mapping for pstack

This document maps portable pstack capabilities (defined in [`pstack-portability`](../../../openspec/specs/pstack-portability/spec.md)) directly to Grok Build native primitives and execution conventions. Structured definitions are formalized in [`profiles/grok.json`](../../../profiles/grok.json).

## Tool actions

| Portable Capability | Grok Build Primitive | Claude Code Equivalent | Antigravity Equivalent |
| --- | --- | --- | --- |
| Read / edit / shell / search | `read_file`, `edit_file`, `write_to_file`, `run_command` | Read / Edit / Bash | `view_file`, `replace_file_content`, `run_command` |
| Fetch a URL / web search | `read_url_content`, `search_web` | WebFetch / WebSearch | `read_url_content`, `search_web` |
| Invoke a skill | Plugin `skills/` `SKILL.md` via `/name` | Skills load natively | Progressive discovery |
| `agent.spawn` | `spawn_subagent` (wire alias `task`) | `Agent` | `invoke_subagent` |
| `agent.fan_out` | N `spawn_subagent` in one turn | N `Agent` in one turn | N in `Subagents` array |
| `agent.join` | `get_command_or_subagent_output` | wait on Agent handles | `manage_subagents` / reactive messaging |
| `agent.message` | Inter-agent message / parent routing | `send_message` | `send_message` |
| `agent.cancel` | `kill_command_or_subagent` (wire alias `kill_task`) | cancel child handle | `manage_task` (kill) |
| `agent.resume` | `spawn_subagent (resume_from)` | resume session | `invoke_subagent` with task context |
| `workspace.shared` | `isolation: "none"` | shared repo root | `Workspace: "inherit"` |
| `workspace.isolated` | `isolation: "worktree"` | git worktree | `Workspace: "branch"` |
| `workspace.readonly` | `pstack:how-explorer (no file-edit tools)` | read-only subagent | `Workspace: "share"` (read-only tools) |
| `task.background` | `spawn_subagent` `background: true`, `monitor` | background jobs | `manage_task`, `schedule` |
| `schedule` | `scheduler_create` (expanded from `/loop`) | `loop` | `schedule` |
| `monitor` | `monitor` (command, description, timeout_ms, persistent) | process watcher | `manage_task`, background jobs |
| `tool.mcp` | Session MCP client | MCP tools | `call_mcp_tool` |
| `plan.update` | `todo_write` | todolist | artifacts / `todo.md` |
| `human.ask` | `ask_user_question` | `AskUserQuestion` | `ask_question` |
| `human.gate` | `ask_user_question (blocking gate)` | blocking confirm | `ask_question` |

## Subagent policy

- Subagent dispatch uses `spawn_subagent`. Parent owns every spawn.
- Recursion depth is capped at 1. Child sessions must not spawn subagents.
- Writers isolate with git worktrees (`isolation: "worktree"`).
- Periodic audit ticks and heartbeats use `scheduler_create` (expanded from `/loop`).
- Pass file pointers instead of inlined dumps.
- Model defaults to `grok-4.6` unless overridden in `~/.grok/pstack-models.toml`.
- Subagent cancellation uses `kill_command_or_subagent` (`kill_task`).

## Wire aliases

- Wire alias for `spawn_subagent` is `task` or `Task`.
- Wire alias for `background` is `run_in_background`.
- Wire alias for `get_command_or_subagent_output` is `get_task_output`.
- Wire alias for canceling subagents is `kill_task`.
