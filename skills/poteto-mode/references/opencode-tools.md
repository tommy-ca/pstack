# OpenCode tool mapping for pstack

This document maps portable pstack capabilities (defined in [`pstack-portability`](../../../openspec/specs/pstack-portability/spec.md)) directly to OpenCode native primitives and execution conventions.

## Tool actions

| Portable Capability | OpenCode Primitive | Claude Code Equivalent | Grok Reference |
| --- | --- | --- | --- |
| Read / edit / shell / search | `terminal`, `file_edit`, `ripgrep` | Read / Edit / Bash | `run_command`, `write_to_file` |
| Fetch a URL | `curl` via `terminal` | WebFetch / Bash | `read_url_content` |
| Invoke a skill | Skills load natively via extension package | Skills load natively | Skills load natively |
| `agent.spawn` | `task.spawn` | `Agent` | `spawn_subagent` |
| `agent.fan_out` | N `task.spawn` in one turn | N `Agent` in one turn | N `spawn_subagent` in one turn |
| `agent.join` | `task.wait` | wait on Agent handles | `get_command_or_subagent_output` |
| `plan.update` | `workbench.plan` / `todo.md` | todolist | `todo_write` |
| `human.ask` | `window.showInputBox` / chat | `AskUserQuestion` | `ask_user_question` |

## Subagent policy

- Subagent dispatch uses OpenCode task runtime.
- Writers isolate with git worktrees (`workspace.isolated`).
- Depth is capped at 1; parent owns every spawn.
- File pointers are passed instead of inlined dumps.
