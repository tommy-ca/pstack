# Grok Build harness

pstack's 22 playbooks and 21 principles stay. Only harness call sites change.

Sources: official pstack (`cursor/plugins` `pstack/`), this TUI (`~/.grok/docs/user-guide/`), and grok-build crates. **Playbooks copy the TUI column.** Rust ids are aliases, not a second live schema.

## Verdict

**Yes.** The discipline ports. The Cursor plugin runtime does not.

Install this repo as a Grok Build plugin. Do not keep `.cursor-plugin`, `~/.cursor/rules/*.mdc`, Cursor `Task`, or Cursor Cloud Agents.

## Mapping: pstack need → grok-build primitive

| pstack need | grok-build primitive | Source |
|---|---|---|
| Slash skill / playbook router | Plugin `skills/` `SKILL.md`. Invoked as `/name`. Frontmatter: `name`, `description`, `disable-model-invocation`, `user-invocable`. | `crates/codegen/xai-grok-pager/docs/user-guide/08-skills.md` |
| Plugin install | `plugin.json` at repo root. grok 1.0.13 `PluginManifest` has **14** parsed fields (extras ignored). This plugin sets `name`, `version`, `description`, `author`, `homepage`, `repository` (string), `license`, `keywords`, `skills`, `agents`. No `commands/`, `hooks/`, `.mcp.json`, `.lsp.json`. `displayName` is not deserialized. Writes `~/.grok/installed-plugins/` (writable in the agent sandbox). | `crates/codegen/xai-grok-agent/src/plugins/manifest.rs`; `09-plugins.md` |
| Marketplace add / plugin enable | Nested `grok plugin marketplace add` and `grok plugin enable` rewrite `~/.grok/config.toml`. Under Linux bubblewrap (`__GROK_INSIDE_BWRAP=1`, `[sandbox] profile = homelab` extends `workspace`) that file is bind-mounted **read-only** with `managed_config.toml`, `sandbox.toml`, `hooks/`. The syscall is `open(config.toml, O_WRONLY\|O_TRUNC) = EROFS` (os error 30). The disk is not remounted ro. `touch` of new files under `~/.grok/` still works. Run add/enable from a **host shell** outside the TUI, or append `[[marketplace.sources]]` by hand. `18-sandbox.md` documents hook write-deny; this TUI also pins config files. | `18-sandbox.md`; `~/.grok/sandbox.toml` `[profiles.homelab]` |
| Spawn a child | TUI tool **`spawn_subagent`**. Rust/wire alias `task` / `Task`. Playbooks send `spawn_subagent`. | `16-subagents.md`; rust `TASK_TOOL_NAME` |
| Background child | TUI field **`background`** (default **false**). Rust alias `run_in_background` (crate default true). Returns `subagent_id`. | `16-subagents.md`; `TaskToolInput` |
| Wait for child | TUI **`get_command_or_subagent_output`** with `task_ids` and `timeout_ms` > 0 to block, omit/`0` to poll. Rust alias `get_task_output`. | `16-subagents.md` |
| Cancel child | `kill_command_or_subagent` / rust `kill_task` with `task_id`. | `16-subagents.md`; `task.rs` |
| Child role | `task.subagent_type`. Built-ins: `general-purpose` (default), `explore`, `plan`. Plugin agents on grok 1.0.13: **`pstack:<role-key>`** (`pstack:feature`, `pstack:how-explainer`, `pstack:poteto-agent`, `pstack:comment-sicko`, `pstack:independent-verifier`, …). Bare keys are unknown. Overlay stem is `~/.grok/roles/pstack:<key>.toml`. Plugin must be in `[plugins].enabled` (`grok plugin enable pstack` from a host shell). `inspect` `plugins[].enabled` is trust, not that list. | `TaskToolInput`; `16-subagents.md`; `xai-grok-agent/src/discovery.rs`; `select_role` |
| Per-spawn model | `task.model` (optional slug). Omit to inherit parent. Do not pass with `resume_from`. Invalid slugs fail via `TaskModelValidator`. | `TaskToolInput.model` |
| Per-spawn reasoning effort | **Not on the model-facing `task` schema.** `TaskToolInput` has no `reasoning_effort` field. Spawn from `task` sets `SubagentRuntimeOverrides.reasoning_effort` to `None`. Out of the box, plugin role agents set `AgentDefinition.effort` in frontmatter from the ship-time three-tier split in [`skills/setup-pstack/references/effort-ladder.md`](./skills/setup-pstack/references/effort-ladder.md) (`xhigh` / `high` / `medium` from the grok 1.0.13 CLI `use one of: xhigh, high, medium, low` list). Do not use `Effort::VALID_VALUES` (reserved `max` is not usable on this CLI). `/setup-pstack` re-detects from live `use one of:` and may overlay `SubagentRole.reasoning_effort` in `~/.grok/roles/pstack:<key>.toml`, which wins. `select_role(subagent_type)` then `apply_definition_runtime_defaults` in `resolve_runtime_config`. Skills spawn `subagent_type` `pstack:<role-key>`. Spawn skills cannot send `task.reasoning_effort` (no field). Do not offer `max` unless the live CLI listed it. Do not invent `ultra`. | `xai-tool-types/src/task.rs` `TaskToolInput`; `task/mod.rs` spawn (`reasoning_effort: None`); `xai-grok-subagent-resolution/src/definition.rs` `select_role` / `resolve_runtime_config` / `apply_definition_runtime_defaults`; live CLI `--reasoning-effort` `use one of:`; `SubagentRole.reasoning_effort`; `handle_request.rs` sampling apply; `~/.grok/roles` in `SubagentsConfig::resolve_base_with_sources` |
| Read-only child | **Not `task.capability_mode`.** That field is `#[schemars(skip)]` and JSON that sends it is **ignored**. Spawn `pstack:how-explorer` (no file-edit tools). Builtin `explore` only if that plugin agent is unknown. | `TaskToolInput.capability_mode`; `apply_child_tool_policy` |
| Worktree isolation | `task.isolation`: `"none"` (default, shared cwd) or `"worktree"`. Mutually exclusive with `task.cwd`. | `SubagentIsolationMode`; `TaskToolInput.isolation` |
| Resume a finished child | `task.resume_from` = prior `subagent_id`. Same `subagent_type`. | `TaskToolInput.resume_from` |
| Nested spawn | **Forbidden by default.** `MAX_SUBAGENT_DEPTH` is `1`. A child that calls `task` fails. The parent session owns every spawn. Playbook "delegate then how/swarm from the child" is rewritten: parent fans out. | `task/mod.rs` `MAX_SUBAGENT_DEPTH` |
| Todo list | `todo_write` with `merge` (default true) and `todos: [{id, content?, status?}]`. Status: `pending`, `in_progress`, `completed`, `cancelled`. | `xai-grok-tools/.../todo/mod.rs` |
| Ask the human (product/preference only) | `ask_user_question` with `questions: [{question, options: [{label, description, preview?}], multi_select?}]`. Not Cursor `AskQuestion`. | `ask_user_question/mod.rs` tool id `ask_user_question`; `AskUserQuestionInput` |
| Recurring overnight loop | Slash `/loop` expands to **`scheduler_create`**. Fields: `interval` (`5m`/`2h`/`1d`, min 60s), `prompt`, `durable?`, `foreground?`, `fire_immediately` (default false; `/loop` instruction sets true). Update in place with `task_id`. Cancel with `scheduler_delete` `{id}`. One-shot delayed work is `sleep && cmd` in a background shell, not the scheduler. | `xai-grok-tools-api/src/slash_commands.rs`; `scheduler/create.rs`; `scheduler/delete.rs` |
| Watch a process / PR | `monitor` with `command`, `description`, `timeout_ms?` (default 10h), `persistent?`. Kill with `kill_task`. Do not poll. | `monitor/tool.rs`; `monitor/types.rs` `MonitorInput` |
| Model per pstack role | Shipped default `grok-4.6` when `~/.grok/pstack-models.toml` is absent (skills send it; omit if `task` rejects). `/setup-pstack` writes that toml as an override. Absent key / `inherit-parent` / `auto`: omit `task.model`. Never write Cursor rules files. Optional extra: `[subagents.models]` in `~/.grok/config.toml` only maps **agent types** (`explore`, `plan`), not pstack roles. | `setup-pstack/SKILL.md`; `defaults.toml`; grok-build `[subagents.models]` in `16-subagents.md` |
| Effort per pstack role | Plugin agents ship frontmatter `effort` from [`effort-ladder.md`](./skills/setup-pstack/references/effort-ladder.md). Setup re-detects the live enum, writes `[effort]` in the toml and `~/.grok/roles/pstack:<key>.toml` (`description` + `reasoning_effort` only). Overlay wins over frontmatter. Skills spawn `pstack:<role-key>` and do not send `task.reasoning_effort`. | `setup-pstack/SKILL.md`; `effort-ladder.md`; `resolve-effort.md`; `agents/<role>.md` |
| Independent verify | Parent calls `task` with `subagent_type: "pstack:independent-verifier"`. No toml: `grok-4.6`. Send a **different** `model` when toml `independent-verifier` is a detected slug ≠ the writer; otherwise omit `model` when inherit-parent. Effort is frontmatter `xhigh` unless setup overlaid `~/.grok/roles/pstack:independent-verifier.toml`. `isolation: "worktree"` when the child must not touch the writer's tree. The verifier does not write the diff. Not a Cursor Cloud Agent. | this file; `agents/independent-verifier.md`; `resolve-effort.md` |
| Cursor Cloud `environment: "cloud"` | Dropped. Use `isolation: "worktree"` plus `run_in_background: true`. | `TaskToolInput.isolation` |
| Graphite `gt` / `graphite-base` | Optional if `gt` is on PATH. Otherwise `gh` + git. Playbook steps stay; the CLI is not assumed. | playbooks, rewritten call sites |
| `cursor-team-kit` (`deslop`, `control-ui`, `control-cli`) | Not in this plugin. `/unslop` and `/no-comments` remain. Drive the real app yourself (browser, CLI, tests). | pstack README "not shipped here" |
| Benny automations | Cursor automation pack. Grok equivalent is plugin `hooks/` + workflows. Not registered as slash skills. Left under `automations/benny/` as source, not a Grok automation runtime. | pstack `automations/benny/`; grok `hooks/hooks.json` |

## Skill order

Playbooks pick **pstack, then user, then bundled and builtin**. Do not add plugin `commands/` clones.

Live user/bundled means the name is in `grok inspect --json` `.skills[].name`. Builtin slash/agent names come from `04-slash-commands.md` / `16-subagents.md`. Skip a column when that layer has no similar skill.

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

## Plugin schema

grok 1.0.13 parses `PluginManifest` (14 fields). Extra JSON keys are ignored. Live serde: `name` (required kebab), `version`, `description`, `author` `{name?, email?, url?}`, `homepage`, `repository` **string only**, `license`, `keywords`, `skills`/`commands`/`agents` as path or path list, `hooks`/`mcpServers`/`lspServers` as path or inline. Convention dirs without those keys: `skills/`, `commands/`, `agents/`, `hooks/hooks.json`, `.mcp.json`, `.lsp.json`.

`AgentDefinition` has 27 fields. Plugin agents must not declare `mcpServers` or `hooks`, and must not set `permissionMode: bypassPermissions`. Valid `permissionMode`: `default`, `acceptEdits`, `dontAsk`, `bypassPermissions`. Do not ship `permissionMode: plan`. Spawn background is `spawn_subagent` `background`, not agent YAML `background:`.

Skill YAML (docs `08-skills.md`): `name`, `description`, `when-to-use`, `allowed-tools`, `argument-hint`, `user-invocable`, `disable-model-invocation`, `model`, `effort`, `license`, `compatibility`, `metadata`. Do not add plugin `commands/` clones of slash skills.

Workflows are `.grok/workflows/*.rhai`, not a plugin component. `plugin-index.json` is catalog display-only unless `GROK_MARKETPLACE_REQUIRE_SHA`.

## Docs vs source

Grok Build's user guide `16-subagents.md` still names `spawn_subagent`, a `background` field defaulting to `false`, and `get_command_or_subagent_output`. The Rust types this port follows are different:

- Canonical tool id is `task` (`TASK_TOOL_NAME`). Wire aliases `Task` and `spawn_subagent` resolve to the same tool.
- Background field is `run_in_background`, default **true**.
- Join with `get_task_output` (`task_ids`, optional `timeout_ms`). `wait_tasks` exists as compatibility; prefer `get_task_output`.
- `scheduler_create.recurring` is `#[schemars(skip)]`. Sending `recurring: false` is rejected; one-shot delay is background `sleep && cmd`.

Playbooks on **this TUI** copy `16-subagents.md`: `spawn_subagent`, `background`, `get_command_or_subagent_output`. The rust field names below stay as aliases.

## `task` fields the model may send

From `TaskToolInput` in `crates/common/xai-tool-types/src/task.rs`:

- `prompt` (string, required)
- `description` (string, required, 3–5 words)
- `subagent_type` (string, default `general-purpose`)
- `run_in_background` (bool, default **true**)
- `isolation` (`none` \| `worktree`, optional)
- `resume_from` (string, optional)
- `cwd` (string, optional; not with `isolation: worktree`)
- `model` (string, optional)

Do not send `readonly`, `environment`, `capability_mode`, or `reasoning_effort` on `task`. They are not model-facing fields. `capability_mode` on the struct is skipped in JSON and ignored if present. Per-role effort is `AgentDefinition.effort` on the plugin agent, overridable by `SubagentRole.reasoning_effort` in `~/.grok/roles/pstack:<key>.toml` when the file stem equals `subagent_type`.

## Default spawn shape

Parent session only:

```text
spawn_subagent
  prompt: <full brief, file pointers not inlined dumps>
  description: <3-5 words>
  subagent_type: pstack:<role-key>   # e.g. pstack:feature | pstack:how-explainer | pstack:independent-verifier | pstack:poteto-agent | pstack:comment-sicko
  background: true   # when the parent must keep working; this TUI defaults false
  model: <slug from ~/.grok/pstack-models.toml when that key is a detected slug; grok-4.6 when the toml is absent; omit if inherit-parent/auto or if grok-4.6 is rejected>
  isolation: none | worktree
```

Do not send `reasoning_effort` or `capability_mode` on that call. Effort is the matching `~/.grok/roles/<subagent_type>.toml` when setup wrote a level, else the plugin agent's frontmatter `effort`.

Then `get_command_or_subagent_output` with `task_ids` and a positive `timeout_ms` when the parent must join.

Code-writing delegates: `pstack:<playbook-role>` (`pstack:feature`, `pstack:bug-fix`, …). Ad-hoc helpers with no role key: `pstack:poteto-agent`.
Read-only codebase walks: `pstack:how-explorer` / `pstack:how-explainer` / `pstack:how-critics` (not the built-in `explore`, so role effort can apply).
MCP-backed `why` investigators: `pstack:why-investigators` / `pstack:why-synthesizer`. Instruct no writes in the prompt. Posture, not a sandbox.
`/no-comments`: `pstack:comment-sicko`.
Independent verify: `pstack:independent-verifier` plus toml key `independent-verifier` when that key is a detected slug different from the writer; no toml: `grok-4.6`. Effort from frontmatter `xhigh` unless overlaid.
