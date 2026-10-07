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

## Skill order

Playbooks pick **pstack, then user, then bundled and builtin**. Do not add plugin `commands/` clones.

| Need | 1. pstack | 2. User | 3. Bundled / builtin |
|---|---|---|---|
| TDD | `/tdd` | `/test-driven-development` only if `/tdd` is not loaded | none |
| Author a SKILL.md | `playbooks/authoring-a-skill.md` | `/writing-skills` | `/create-skill` |
| Review a diff or PR | `/interrogate` | `/requesting-code-review` | `/review` |
| Babysit | `playbooks/babysit.md` | none | none |
| Prove work is done | **prove-it-works**, `pstack:independent-verifier` | `/verification-before-completion` | none |
| Debug a failure | `playbooks/bug-fix.md` | `/systematic-debugging` | none |
| Disk prune | `playbooks/worktree-cleanup.md` | none | none |
| Worktree isolation | none | `/using-git-worktrees` | `isolation: "worktree"` |
| Design a playbook | `/figure-it-out` (`skills/figure-it-out/SKILL.md`) | none | none |
| Spec then plan | none | `/brainstorming`, `/writing-plans` | `/plan`, builtin `plan` |
| Execute a written plan | `playbooks/feature.md` spawn | `/executing-plans`, `/subagent-driven-development` | `/implement`, `/execute-plan` |
| Overnight heartbeat | none | none | `/loop` → `scheduler_create` |
| Read-only spawn | `pstack:how-explorer` | none | builtin `explore` if plugin agent unknown |
| Unslop / comments | `/unslop`, `/no-comments` | none | none |

Do not route babysit to `/pr-babysit`. That skill restacks. pstack `babysit.md` forbids topology mutation. User TDD is not a substitute when `/tdd` skipped the cheap-path gate.

## Subagent policy

- Subagent dispatch uses `spawn_subagent`. Parent owns every spawn.
- Rust wire alias is `task` / `Task` (`TASK_TOOL_NAME`).
- Recursion depth is capped at 1: `MAX_SUBAGENT_DEPTH` is `1`. A child that calls `task` fails. The parent session owns every spawn.
- Background execution uses `background: true` (wire alias `run_in_background`). Returns `subagent_id`.
- Waiting uses `get_command_or_subagent_output` with `task_ids` and `timeout_ms` > 0 to block, omit or `0` to poll (wire alias `get_task_output`).
- Subagent cancellation uses `kill_command_or_subagent` (wire alias `kill_task`).
- Writers isolate with git worktrees (`isolation: "worktree"`).
- Periodic audit ticks and heartbeats use `scheduler_create` (expanded from `/loop`).
- Pass file pointers instead of inlined dumps.
- Model defaults to `grok-4.6` unless overridden in `~/.grok/pstack-models.toml`.
- Child roles use `task.subagent_type`: built-in `general-purpose` (default), `explore`, `plan`; plugin agents: `pstack:<role-key>` (`pstack:feature`, `pstack:how-explainer`, `pstack:poteto-agent`, `pstack:comment-sicko`, `pstack:independent-verifier`, …). Bare keys are unknown. Overlay stem is `~/.grok/roles/pstack:<key>.toml`.
- Effort ladder resolution: plugin agents ship frontmatter `effort` per [`effort-ladder.md`](../../setup-pstack/references/effort-ladder.md). Setup may overlay `SubagentRole.reasoning_effort` in `~/.grok/roles/pstack:<key>.toml`. Resolver uses `select_role(subagent_type)` and `apply_definition_runtime_defaults` in `resolve_runtime_config` for `AgentDefinition`.
- Independent verify uses `pstack:independent-verifier` with model from toml when different from the writer; frontmatter effort `xhigh` unless overlaid.
- Per-spawn model: `task.model` is an optional slug; omit it to inherit the parent, and do not pass `model` together with `resume_from`. Invalid slugs fail via `TaskModelValidator` (`TaskToolInput.model`).
- Resume a finished child with `task.resume_from` set to the prior `subagent_id`, using the same `subagent_type` (`TaskToolInput.resume_from`).

## Scheduler and delayed work

`/loop` expands to `scheduler_create` (source: `xai-grok-tools-api/src/slash_commands.rs`). Fields: `interval` (`5m`/`2h`/`1d`, minimum 60 seconds), `prompt`, optional `durable`/`foreground`, and `fire_immediately` (default false; the `/loop` instruction sets it true). Update in place with `task_id`; cancel with `scheduler_delete` `{id}` (`scheduler/create.rs`; `scheduler/delete.rs`). `scheduler_create.recurring` is `#[schemars(skip)]` in the Rust schema, so sending `recurring: false` is rejected. One-shot delayed work is `sleep && cmd` in a background shell, not scheduler recurring work.

## Default spawn shape

Parent session only:

```text
spawn_subagent
  prompt: <full brief, file pointers not inlined dumps>
  description: <3-5 words>
  subagent_type: pstack:<role-key>   # e.g. pstack:feature | pstack:how-explainer | pstack:independent-verifier | pstack:poteto-agent | pstack:comment-sicko
  background: true   # when the parent must keep working; default false
  model: <slug from ~/.grok/pstack-models.toml or grok-4.6>
  isolation: none | worktree
```

## `task` fields the model may send

From `TaskToolInput`:
- `prompt` (string, required)
- `description` (string, required, 3-5 words)
- `subagent_type` (string, default `general-purpose`)
- `run_in_background` (bool, default true)
- `isolation` (`none` | `worktree`, optional)
- `resume_from` (string, optional)
- `cwd` (string, optional; not with `isolation: worktree`)
- `model` (string, optional)

Do not send `readonly`, `environment`, `capability_mode`, or `reasoning_effort` on `task`. They are not model-facing fields.

## Plugin schema and packaging

Under the 5-harness package architecture (`pstack.package.json`), package manifests are projected via `scripts/project-package.py` to `.grok-plugin/plugin.json` while maintaining repository root `plugin.json` in parity for single-host grok CLI discovery and validation (`grok plugin validate`). grok 1.0.13 parses `PluginManifest` (14 fields). Extra JSON keys are ignored.

Plugin agents must not declare `mcpServers` or `hooks`, and must not set `permissionMode: bypassPermissions`. Valid `permissionMode`: `default`, `acceptEdits`, `dontAsk`, `bypassPermissions`. Do not ship `permissionMode: plan`.

Workflows are `.grok/workflows/*.rhai`, not a plugin component. grok-build `PluginManifest` has no `workflows` field.

## Install, enable, and sandbox

Install this repo as a Grok Build plugin: `grok --sandbox off plugin install tommy-ca/pstack --trust`. Marketplace add is catalog-only; it does not install pstack. `grok plugin enable pstack` rewrites `~/.grok/config.toml`. If the sandbox returns `EROFS`, run that one host-shell command with `grok --sandbox off`. After enable, `grok inspect --json` `.agents[].name` must include `pstack:swarm-workers`. Inspect `plugins[].path` and `skills[]` `collidesWith` name the install tree and skill overlays. Missing `pstack:swarm-workers` means Grok is not loading this checkout (`tommy-ca/pstack`).

## Herdr integration

Install or update with `herdr integration install grok` from a host shell or `grok --sandbox off`. The built-in `workspace` sandbox (and dev-env `homelab`) permits callback delivery with hook files read-only; the callback writes temporary state and reports through `$HERDR_SOCKET_PATH`. In dev-env, the source-managed Bash/Zsh helper is loaded only when `HERDR_ENV=1` and sets `HERDR_AGENT=grok` before the real binary, so launch plain `grok --sandbox workspace --no-alt-screen`. Herdr should report `herdr:grok` and `agent_status: idle` in both `herdr pane get` and `herdr agent list`. For a standalone pstack checkout, use explicit `env HERDR_AGENT=grok ...` instead. An explicit `command grok ...` bypass is a negative control and may report `agent_status: unknown`; the hint is detection-only, not a sandbox permission or callback-delivery grant. Supported profiles are `workspace`, `devbox`, `read-only`, `strict`, plus dev-env `homelab`; no custom Herdr setup profile is supported. Do not add hook or Herdr-socket write grants.

## Benny automations

The Cursor pack under `automations/benny/skills/` is the upstream reference. The live grok contract is `automations/benny-grok/` (`/benny-triage`, `/benny-repro` via the plugin `skills` list). Enable pstack. No copy. Not plugin `hooks`. Spawn `pstack:<role>` via `spawn_subagent`. `/loop` expands to `scheduler_create`. Slack auto-start is a host gap.

## Forge and PR stack

Resolve once. GitHub CLI (`gh`) is the default. If `command -v origin` succeeds and Origin resolves the repository, use `origin pr` for PR operations; otherwise record the `gh pr` fallback per [github-pr-fallback.md](github-pr-fallback.md). Stacked work uses explicit parent base branches. Never require Graphite `gt`; never use `--auto` on a child PR.

## Wire aliases

- Wire alias for `spawn_subagent` is `task` or `Task`.
- Wire alias for `background` is `run_in_background`.
- Wire alias for `get_command_or_subagent_output` is `get_task_output`.
- Wire alias for canceling subagents is `kill_task`.
