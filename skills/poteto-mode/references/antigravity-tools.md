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

## Models

Antigravity model routing spans two dispatch surfaces, configured at `~/.gemini/config/pstack-models.md` and projected into `.antigravity-plugin/models.json`:

- **Subagent dispatch (`invoke_subagent`)**: accepts the schema tier enum values `pro`, `flash`, `flash_lite`, and `inherit`.
- **CLI and Swarm dispatch (`agy --model` / `swarm(action="add", model=...)`)**: accepts concrete catalog slugs detected by `agy models` and `swarm(action="models", all=True)`.

### Model tiers

1. **Main reasoning driver (`gemini-4-hydrogen-high` / `gemini-4-hydrogen-xhigh`, `pro` tier)**: Primary frontier workhorse for orchestration, architecture, synthesis, feature implementation, debugging, refactoring, and independent verification.
2. **Main fast worker and verifier driver (`gemini-3.8-flash-high` / `gemini-3.8-flash-medium` / `gemini-3.8-flash-low`, `flash` and `flash_lite` tiers)**: High-throughput, low-latency driver for codebase exploration (`how-explorer`), evidence collection (`why-investigators`), parallel workers (`swarm-workers`), comment cleanup (`comment-sicko`), and panel contrast (`pro, flash`).
3. **Paid Pro subscription tier when available (`gemini-4-argon-high` / `gemini-pro-orchestrator-g1-pro`)**: Drop-in paid Pro subscription upgrade for `pro` orchestration (`poteto-agent`), architecture (`architect-runners`), synthesis (`why-synthesizer`, `judgment-and-prose`), and independent verification (`independent-verifier`).
4. **Minimal specialist tier (`claude-opus-5-5-high`)**: Used strictly at minimal for `hardest-tasks` or an explicit cross-family adversarial seat when requested, never as a default or bulk driver.

### Role mappings

Rows are the canonical role IDs from `pstack.package.json#/roles`, projected into `.antigravity-plugin/models.json`.

| Role | Skill | Subagent Tier (`invoke_subagent`) | Main CLI / Swarm Driver | Paid Pro Sub Driver (When Available) | Notes |
| --- | --- | --- | --- | --- | --- |
| `architect-runners` | `architect` | `pro, flash` (panel) | `gemini-4-hydrogen-high`, `gemini-3.8-flash-high` | `gemini-4-argon-high`, `gemini-3.8-flash-high` | Architecture sketch panel |
| `arena-cross-judge-pool` | `arena` | `pro, flash` (panel) | `gemini-4-hydrogen-high`, `gemini-3.8-flash-high` | `gemini-4-argon-high`, `gemini-3.8-flash-high` | Evaluation and cross-judging |
| `arena-runners` | `arena` | `pro, flash` (panel) | `gemini-4-hydrogen-high`, `gemini-3.8-flash-high` | `gemini-4-argon-high`, `gemini-3.8-flash-high` | Multi-candidate authoring |
| `bug-fix` | `poteto-mode` | `pro` | `gemini-4-hydrogen-high` | `gemini-4-argon-high` | Root-cause defect fixes |
| `comment-sicko` | `poteto-mode` | `flash` | `gemini-3.8-flash-high` | `gemini-3.8-flash-high` | High-volume comment deletion |
| `feature` | `poteto-mode` | `pro` | `gemini-4-hydrogen-high` | `gemini-4-argon-high` | Feature implementation |
| `hardest-tasks` | `poteto-mode` | `pro` | `gemini-4-hydrogen-xhigh` (`claude-opus-5-5-high` minimal) | `gemini-4-argon-high` (`claude-opus-5-5-high` minimal) | Deepest reasoning escalation |
| `hillclimb` | `poteto-mode` | `pro` | `gemini-4-hydrogen-high` | `gemini-4-argon-high` | Iterative metric optimization |
| `how-critics` | `how` | `pro` | `gemini-4-hydrogen-high` | `gemini-4-argon-high` | Read-only design critique |
| `how-explainer` | `how` | `pro` | `gemini-4-hydrogen-high` | `gemini-4-argon-high` | Subsystem explanation prose |
| `how-explorer` | `how` | `flash` | `gemini-3.8-flash-high` | `gemini-3.8-flash-high` | Read-only codebase traversal |
| `independent-verifier` | `poteto-mode` | `pro` | `gemini-4-hydrogen-high` | `gemini-4-argon-high` | Read-only verification gate |
| `interrogate-reviewers` | `interrogate` | `pro, flash` (panel) | `gemini-4-hydrogen-high`, `gemini-3.8-flash-high` | `gemini-4-argon-high`, `gemini-3.8-flash-high` | Optional `claude-opus-5-5-high` cross-family seat when requested |
| `judgment-and-prose` | `poteto-mode` | `pro` | `gemini-4-hydrogen-high` | `gemini-4-argon-high` | Judgment and synthesis prose |
| `perf-issue` | `poteto-mode` | `pro` | `gemini-4-hydrogen-high` | `gemini-4-argon-high` | Profiling and latency fixes |
| `poteto-agent` | `poteto-mode` | `pro` | `gemini-4-hydrogen-high` | `gemini-pro-orchestrator-g1-pro` / `gemini-4-argon-high` | Delegated orchestrator worker |
| `refactoring` | `poteto-mode` | `pro` | `gemini-4-hydrogen-high` | `gemini-4-argon-high` | Fast tier eligible only when `< 100` LOC and tested |
| `reflect-judgment` | `reflect` | `pro` | `gemini-4-hydrogen-high` | `gemini-4-argon-high` | Transcript judgment review |
| `reflect-tooling` | `reflect` | `pro` | `gemini-4-hydrogen-high` | `gemini-4-argon-high` | Tooling and skill audit |
| `swarm-workers` | `swarm` | `flash` | `gemini-3.8-flash-high` | `gemini-3.8-flash-high` | Parallel bounded workers (`gemini-3.8-flash-medium` for light sweeps) |
| `why-investigators` | `why` | `flash` | `gemini-3.8-flash-high` | `gemini-3.8-flash-high` | Parallel evidence gathering |
| `why-synthesizer` | `why` | `pro` | `gemini-4-hydrogen-high` | `gemini-4-argon-high` | Decision rationale synthesis |

### Eliminated models

`gpt-oss-*` (such as `gpt-oss-120b-medium`) is strictly eliminated from all `pstack` Antigravity model catalogs, panels, role assignments, and override templates. Keep `claude-*` (`claude-opus-5-5-high`) restricted strictly to minimal `hardest-tasks` or explicit cross-family review seats rather than routine execution.
