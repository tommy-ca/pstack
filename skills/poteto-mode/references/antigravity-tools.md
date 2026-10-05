# Antigravity tool mapping for pstack

This document maps portable pstack capabilities (defined in [`pstack-portability`](../../../openspec/specs/pstack-portability/spec.md)) directly to Google Antigravity (`antigravity-cli` / `agy`) native primitives and execution conventions.

## Tool actions

| Portable Capability | Antigravity Primitive | Claude Code Equivalent | Grok Reference |
| --- | --- | --- | --- |
| Read / edit / shell / search | `view_file`, `replace_file_content`, `write_to_file`, `run_command` | Read / Edit / Bash | `run_command`, `write_to_file` |
| Fetch a URL / web search | `read_url_content`, `search_web` | WebFetch / WebSearch | `read_url_content`, `search_web` |
| Invoke a skill | Progressive discovery (`skills/<name>/SKILL.md`) | Skills load natively | Skills load natively |
| `agent.spawn` | `invoke_subagent`, `define_subagent` | `Agent` | `spawn_subagent` |
| `agent.fan_out` | N items in `Subagents` array of `invoke_subagent` | N `Agent` in one turn | N `spawn_subagent` in one turn |
| `agent.join` | `manage_subagents` / reactive messaging | wait on Agent handles | `get_command_or_subagent_output` |
| `agent.message` | `send_message` | `send_message` | inter-agent message |
| `task.background` | `run_command` (async), `manage_task`, `schedule` | background jobs | background tasks |
| `tool.mcp` | `call_mcp_tool`, `list_resources`, `read_resource` | MCP tools | MCP tools |
| `plan.update` | Artifacts (`.md` in artifact dir) / `todo.md` | todolist | `todo_write` |
| `human.ask` | `ask_question` | `AskUserQuestion` | `ask_user_question` |

## Subagent policy

- Subagent dispatch uses native `invoke_subagent` with explicit `TypeName`, `Role`, `Prompt`, `Workspace`, and `Model`.
- Isolated workspaces use `Workspace: "branch"` or git worktrees (`workspace.isolated`).
- Read-only inspection uses `Workspace: "share"` with read-only tools.
- Reactive wakeup handles subagent responses without wasteful polling loops.
- File pointers and artifact URIs are passed instead of inlined dumps.
