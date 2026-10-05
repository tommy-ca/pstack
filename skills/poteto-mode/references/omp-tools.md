# OMP tool mapping for pstack

This document maps portable pstack capabilities (defined in [`pstack-portability`](../../../openspec/specs/pstack-portability/spec.md)) directly to Oh-My-Pi (OMP) native primitives and execution conventions.

## Tool actions

| Portable Capability | OMP Primitive | Claude Code Equivalent | Grok Reference |
| --- | --- | --- | --- |
| Read / edit / shell / search | `bash`, `file_edit`, `grep` | Read / Edit / Bash | `run_command`, `write_to_file` |
| Fetch a URL | `web_search`, `fetch` | WebFetch / Bash | `read_url_content` |
| Invoke a skill | Skills load natively via plugin manifest | Skills load natively | Skills load natively |
| `agent.spawn` | `pi_spawn` | `Agent` | `spawn_subagent` |
| `agent.fan_out` | N `pi_spawn` concurrent calls | N `Agent` in one turn | N `spawn_subagent` in one turn |
| `agent.join` | `pi_wait` / task handle | wait on Agent handles | `get_command_or_subagent_output` |
| `plan.update` | `task_tracker` / `todo.md` | todolist | `todo_write` |
| `human.ask` | `pi_prompt` | `AskUserQuestion` | `ask_user_question` |

## Subagent policy

- Subagent dispatch uses native OMP concurrency pools.
- Writers isolate with git worktrees (`workspace.isolated`).
- Depth is capped at 1; parent owns every spawn.
- File pointers are passed instead of inlined dumps.
