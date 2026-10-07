# Codex tool mapping for pstack

This document maps portable pstack capabilities (defined in [`pstack-portability`](../../../openspec/specs/pstack-portability/spec.md)) directly to Codex native primitives and execution conventions. Structured definitions are formalized in [`profiles/codex.json`](../../../profiles/codex.json). Grok reference mapping is maintained separately in [`grok-tools.md`](grok-tools.md); Codex does not inherit Grok vocabulary as an intermediate specification. Model routing is in [`provider-dispatch.md`](provider-dispatch.md).

## Tool actions

| Portable Capability | Codex Primitive | Claude Code Equivalent | Grok Reference |
| --- | --- | --- | --- |
| Read / edit / shell / search | `read_file`, `apply_patch`, `execute_command` | Read / Edit / Bash | `read_file`, `edit_file`, `run_command` |
| Fetch a URL / web search | `fetch_web`, `search_web` | WebFetch / WebSearch | `read_url_content`, `search_web` |
| Invoke a skill | Skills load natively | Skills load natively | Skills load natively |
| `agent.spawn` | `spawn_agent` | `Agent` | `spawn_subagent` |
| `agent.fan_out` | N `spawn_agent` in one turn | N `Agent` in one turn | N `spawn_subagent` in one turn |
| `agent.join` | `wait_agent` | wait on Agent handles | `get_command_or_subagent_output` |
| `agent.message` | `send_message` | `send_message` | `spawn_subagent (resume)` |
| `agent.cancel` | No cancel API (named gap) | cancel child handle | `kill_command_or_subagent` |
| `agent.resume` | `resume_agent` | resume session | `spawn_subagent (resume_from)` |
| `workspace.shared` | `cwd` (shared repo root) | shared repo root | `isolation: none` |
| `workspace.isolated` | `git worktree` | git worktree | `isolation: worktree` |
| `workspace.readonly` | Read-only tools / prompt advisory | read-only subagent | `pstack:how-explorer` |
| `task.background` | `spawn_agent` (implicit async) | background jobs | `spawn_subagent background: true` |
| `schedule` | Scheduled task / cadence loop | `loop` | `scheduler_create` |
| `monitor` | Watch loop / process poll | process watcher | `monitor` |
| `tool.mcp` | `mcp_client` | MCP tools | session MCP client |
| `plan.update` | `update_plan` | todolist | `todo_write` |
| `human.ask` | `plain_text_question` / `request_user_input` | `AskUserQuestion` | `ask_user_question` |
| `human.gate` | Blocking question in plain text | blocking confirm | `ask_user_question (blocking gate)` |

Subagent dispatch on Codex needs `multi_agent` in `~/.codex/config.toml`:

```toml
[features]
multi_agent = true
```

Without it, the native Codex lane is a named dropout. Never collapse a panel into a sequential single-model pass.

## Skill order

Playbooks pick **pstack, then user, then bundled and builtin**. Do not add plugin `commands/` clones.

| Need | 1. pstack | 2. User | 3. Bundled / builtin |
| --- | --- | --- | --- |
| TDD | `/tdd` | `/test-driven-development` only if `/tdd` is not loaded | none |
| Author a SKILL.md | `playbooks/authoring-a-skill.md` | `/writing-skills` | `/create-skill` |
| Review a diff or PR | `/interrogate` | `/requesting-code-review` | `/review` |
| Babysit | `playbooks/babysit.md` | none | none |
| Prove work is done | **prove-it-works**, `pstack:independent-verifier` | `/verification-before-completion` | none |
| Debug a failure | `playbooks/bug-fix.md` | `/systematic-debugging` | none |
| Disk prune | `playbooks/worktree-cleanup.md` | none | none |
| Worktree isolation | none | `/using-git-worktrees` | `isolation: worktree` |
| Design a playbook | `/figure-it-out` | none | none |
| Spec then plan | none | `/brainstorming`, `/writing-plans` | `plan` |
| Execute a written plan | `playbooks/feature.md` spawn | `/executing-plans`, `/subagent-driven-development` | `/implement`, `/execute-plan` |
| Overnight heartbeat | none | none | cadence loop / scheduled task |
| Read-only spawn | `pstack:how-explorer` | none | `explore` |
| Unslop / comments | `/unslop`, `/no-comments` | none | none |

## Subagent policy

Subagent dispatch follows the portable `agent.spawn` and `workspace.isolated` capabilities:

- Codex has no `poteto-agent` type: dispatch `spawn_agent` instructed to read `poteto-mode` first.
- `spawn_agent` is concurrent natively; `run_in_background` is implicit.
- No `comment-sicko` type: dispatch `spawn_agent` instructed to read `agents/comment-sicko.md`.
- Writers isolate with worktrees (`workspace.isolated`: Codex isolated worktree; Grok reference `isolation: worktree`).
- Pass file pointers, not inlined dumps. Parent owns every spawn (depth 1).

## Models

Codex model routing uses detected OpenAI frontier models. Configuration lives at `~/.codex/pstack-models.md` and projected plugin configuration `.codex-plugin/models.json`.

### Model tiers

1. **Frontier reasoning (`gpt-6.1-sol`)**: Flagship reasoning model. Default model for Codex. Assigned to architecture, debugging, performance, hillclimbing, and strongest judgment roles.
2. **Balanced panelist (`gpt-6-astra`)**: Second frontier tier for multi-model diversity. Assigned to arena cross-judge pools, candidate runners, and adversarial review panels.
3. **High-throughput volume (`gpt-6-luna`)**: Fast execution tier. Assigned to routine feature authoring, refactoring, exploration, synthesis, and swarm workers.
4. **Eliminated models**: `gpt-5.6-terra` is obsolete and strictly eliminated from all panels and candidate lists.

### Role mappings

| Role | Target Model | Purpose |
| --- | --- | --- |
| `feature`, `refactoring` | `gpt-6-luna` | Fast execution and volume authoring |
| `bug-fix`, `perf-issue`, `hillclimb` | `gpt-6.1-sol` | Deep reasoning and root cause diagnosis |
| `judgment and prose` | `gpt-6-luna` | Prose drafting and unslop passes |
| `strongest judgment` | `gpt-6.1-sol` | Final verdict and architectural gate |
| `how explorer`, `why investigators` | `gpt-6-luna` | Read-only codebase traversal |
| `how explainer`, `why synthesizer` | `gpt-6-luna` | Structured documentation and explanation |
| `reflect tooling` | `gpt-6-luna` | Tooling audit and lint checking |
| `reflect judgment, divergent, synthesizer` | `gpt-6.1-sol` | Deep structural reflection |
| `arena runners` | `gpt-6.1-sol`, `gpt-6-astra`, `gpt-6-luna` | Multi-model candidate generation |
| `arena cross-judge pool` | `gpt-6.1-sol`, `gpt-6-astra`, `gpt-6-luna` | Diverse evaluation panel |
| `swarm workers` | `gpt-6-luna` | Fast parallel matrix execution |
| `architect runners` | `gpt-6.1-sol`, `gpt-6-astra`, `gpt-6-luna` | Multi-perspective system architecture |
| `interrogate reviewers` | `gpt-6.1-sol`, `gpt-6-astra`, `gpt-6-luna` | Multi-model adversarial review |

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
