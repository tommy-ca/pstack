# Codex tool mapping for pstack

This document maps portable pstack capabilities (defined in [`pstack-portability`](../../../openspec/specs/pstack-portability/spec.md)) directly to Codex native primitives and execution conventions. Grok reference mapping is maintained separately in [`grok-tools.md`](grok-tools.md); Codex does not inherit Grok vocabulary as an intermediate specification. Model routing is in [`provider-dispatch.md`](provider-dispatch.md).

## Tool actions

| Portable Capability | Codex Primitive | Claude Code Equivalent | Grok Reference |
| --- | --- | --- | --- |
| Read / edit / shell / search | `shell`, `apply_patch`, `rg` | Read / Edit / Bash | `run_command`, `write_to_file` |
| Fetch a URL | `shell` with `curl` | WebFetch / Bash | `read_url_content` |
| Invoke a skill | Skills load natively | Skills load natively | Skills load natively |
| `agent.spawn` | `spawn_agent` | `Agent` | `spawn_subagent` |
| `agent.fan_out` | N `spawn_agent` in one turn | N `Agent` in one turn | N `spawn_subagent` in one turn |
| `agent.join` | `wait_agent` | wait on Agent handles | `get_command_or_subagent_output` |
| `plan.update` | `update_plan` | todolist | `todo_write` |
| `human.ask` | Ask in plain text | `AskUserQuestion` | `ask_user_question` |

Subagent dispatch on Codex needs `multi_agent` in `~/.codex/config.toml`:

```toml
[features]
multi_agent = true
```

Without it, the native Codex lane is a named dropout. Never collapse a panel into a sequential single-model pass.

## Subagent policy

Subagent dispatch follows the portable `agent.spawn` and `workspace.isolated` capabilities:

- Codex has no `poteto-agent` type: dispatch `spawn_agent` instructed to read `poteto-mode` first.
- `spawn_agent` is concurrent natively; `run_in_background` is implicit.
- No `comment-sicko` type: dispatch `spawn_agent` instructed to read `agents/comment-sicko.md`.
- Writers isolate with worktrees (`workspace.isolated`: Codex isolated worktree; Grok reference `isolation: worktree`).
- Pass file pointers, not inlined dumps. Parent owns every spawn (depth 1).

## Models

`/setup-pstack` writes **detected** host slugs. On a Codex parent, native `codex:*` uses `spawn_agent`. Other providers are optional outbound runners, not this in-process host. Do not send Cursor marketplace panel slugs as live models.

## Overnight / babysit / shipping

Cursor same-run `/loop` is **not** live.

| Host | Overnight |
| --- | --- |
| Grok Build | Persist trail. Event: `monitor`. Heartbeat: `/loop` → `scheduler_create` (new turn). |
| Claude Code | Built-in `loop` skill. |
| Codex | Re-run the step on a cadence or a Codex scheduled task. |

## Vendored scripts

`skills/poteto-mode/scripts/` is a bounded set of Codex compatibility utilities and the Codex compatibility surface for bun/bash hosts. It includes `orch/orch.ts` plus `orch/store.ts` and tests, `watch-pr/watch-pr` plus its TypeScript reader/policy/tests, `check-plan.mjs`, and `worktree-audit.sh`. Invoke these through `shell`; they are not a Grok durable orchestration surface. Grok uses canonical task and agent state plus `monitor`/`/loop` and Gas City/Beads. `worktree-audit.sh` accepts `PSTACK_TRANSCRIPTS_DIR` when the host supplies a transcript root and otherwise falls back to its historical Cursor path. Transcript paths: Grok `~/.grok/sessions/`; Claude `~/.claude/projects/`; Codex session storage. Not `~/.cursor/projects/`.

## Instructions file

Codex: `AGENTS.md`. Claude Code: `CLAUDE.md`. Grok Build: `AGENTS.md` plus `references/grok-tools.md`.
