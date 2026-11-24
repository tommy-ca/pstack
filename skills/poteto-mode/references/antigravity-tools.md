# Antigravity tool mapping for pstack

This document maps portable pstack capabilities in `openspec/specs/pstack-portability/spec.md` to Google Antigravity CLI (`agy` 1.5.16) primitives and dispatch rules.

## Tool surface split

Antigravity 1.5.16 exposes interactive CLI tool aliases in live sessions and internal tool IDs in headless probes (`agy -p --output-format stream-json`) and hooks (`hooks.json`).

| Portable Capability | Interactive CLI Primitive | Headless and Hook Primitive | Notes |
| --- | --- | --- | --- |
| File read and search | `read_file` | `view_file`, `list_dir`, `find_by_name`, `grep_search` | Hook matchers must target internal IDs |
| File edit | `edit_file` | `replace_file_content`, `multi_replace_file_content` | Multi-hunk edits use `multi_replace_file_content` |
| File write | `write_file` | `write_to_file` | Used for evidence and artifacts |
| Shell execution | `run_command` | `run_command` | Supports async background execution |
| Web fetch and search | `search_web` | `read_url_content`, `search_web` | `read_url_content` appears in headless `init.tools` |
| Skill discovery | Progressive `SKILL.md` | Progressive `SKILL.md` | Discovers `.agents/skills/` and `~/.agents/skills/` (`1.5.16+`) |
| `agent.spawn` | `invoke_subagent`, `define_subagent` | `invoke_subagent`, `define_subagent` | `/swarm` and `run_workflow` add gated modes |
| `agent.fan_out` | N `Subagents` in `invoke_subagent` | `invoke_subagent`, `run_workflow` | Native `swarm` only when `/swarm` active |
| `agent.join` | `manage_subagents`, reactive messaging | `manage_subagents`, `swarm_wait`, `trajectory()` | Reactive wakeup avoids polling loops |
| `agent.message` | `send_message` | `send_message`, `post_message` | `post_message` routes `@name`, `@group`, `@all`, `@#channel` |
| `task.background` | `run_command` (async), `manage_task`, `schedule` | `manage_task`, `schedule` | `schedule` supports `DurationSeconds`, `CronExpression`, `TimerCondition` |
| `tool.mcp` | `call_mcp_tool`, `list_resources`, `read_resource` | `call_mcp_tool`, `list_resources`, `read_resource` | Native MCP boundary |
| `plan.update` | Artifacts, `todo.md`, `/plan` | `swarm_pane` (`plan.json`) | `swarm_pane` replaces `swarm_narrator` |
| `human.ask` | `ask_question`, `/grill-me` | `ask_question` | Blocking interactive gate |

## Subagent and fan-out gating

1. Parent-owned `invoke_subagent` (default). Standard PStack fan-out uses `invoke_subagent` with `TypeName`, `Role`, `Prompt`, `Workspace`, and `Model`. Isolated writers use `Workspace` set to `"branch"`. Read-only inspection uses `Workspace` set to `"share"`. Forbidden fields are `readonly`, `environment`, and `reasoning_effort`. When spawning custom writers with `define_subagent`, set `EnableWriteTools=True` explicitly because read-only roles only expose read, search, MCP, task, and messaging tools.
2. Native `/swarm` gating (`1.5.13+`). Antigravity guards native `swarm` creation behind an explicit `/swarm` invocation or an active swarm board so agents do not spawn quota-heavy swarms unprompted. Use `swarm`, `post_message`, `read_board`, `swarm_wait`, `/swarm board` (`Alt+S`), `swarm_pane`, and `@monitor` (`swarm_monitor`) only when `/swarm` is active. Otherwise route `pstack` `/swarm` through `invoke_subagent` or `run_workflow`.
3. Deterministic `run_workflow` pipelines. Use `/run-workflow` or `run_workflow` for scripted Python phase graphs using `phase()`, `log()`, `agent()`, `parallel()`, `pipeline()`, `trajectory()`, `call_tool()`, `CONVERSATION_ID`, `STEP_INDEX`, `WORKSPACES`, and JSON-Schema `finish` outputs. `run_workflow` accepts per-agent `workspace` (`inherit`, `branch`, `share`) and `model` (`inherit`, `flash_lite`, `flash`, `pro`).

## Depth policy 1 vs runtime 10

Antigravity 1.5.16 permits up to 10 nested subagent levels at runtime. PStack enforces `max_subagent_depth` equal to `1` in `profiles/antigravity.json`, `poteto-mode`, and `provider-dispatch.md`. Only the root coordinator session may call `invoke_subagent`, `swarm`, or `run_workflow`. Depth-1 workers own their diff or read-only verdict directly and never spawn nested children.

## Discrete seats for Arena and Interrogate

Panel skills must assign distinct slugs across seats and never run duplicate copies of one model slug.

| Workflow | Role Key | Tier Panel (`invoke_subagent`) | Discrete CLI or Swarm Seats |
| --- | --- | --- | --- |
| `pstack` `/arena` | `arena-runners`, `arena-cross-judge-pool` | `pro, flash` | `gemini-4-hydrogen-high`, `gemini-3.8-flash-high`, optional `claude-opus-4-6-thinking` or `claude-sonnet-4-6` |
| `pstack` `/interrogate` | `interrogate-reviewers` | `pro, flash` | `gemini-4-hydrogen-high` (or `gemini-4-neon-high`), `gemini-3.8-flash-high`, optional `claude-opus-4-6-thinking` |
| `/architect` | `architect-runners` | `pro, flash` | `gemini-4-hydrogen-high`, `gemini-3.8-flash-high` |

`agy agents` discovers 25 agents locally, consisting of 22 PStack canonical roles plus 3 built-in `jd-*` agents (`jd-fix-agent`, `jd-judge-a`, `jd-judge-b`). Built-in Antigravity role names invoke directly via their bare `TypeName` (such as `arena-runners` or `independent-verifier`). PStack `/interrogate` dispatches `interrogate-reviewers` rather than `jd-*`.

## Models, effort flags, and deprecations

Antigravity separates subagent catalog configuration from CLI session flags.

- Subagent and `.antigravity-plugin/models.json` surface. `setup.source` stays `"host-catalog"` and `setup.effort` stays `"none"`. `invoke_subagent` accepts only `pro`, `flash`, `flash_lite`, and `inherit`.
- CLI and TUI effort surface. Interactive `/effort` and startup `agy --effort` accept `low`, `medium`, `high`, `xhigh`, and `max` on adjustable models. Fixed-budget `Orchestrator` pairings (`gemini-pro-orchestrator-g1-pro` and `--model "Orchestrator (Neon|Carbon|Argon)"`) exclude effort adjustment.
- Live local `agy models` slugs. `gemini-4-hydrogen-low`, `gemini-4-hydrogen-medium`, `gemini-4-hydrogen-high`, `gemini-4-hydrogen-xhigh`, `gemini-3.8-flash-low`, `gemini-3.8-flash-medium`, `gemini-3.8-flash-high`, `claude-opus-4-6-thinking`, and `claude-sonnet-4-6`.
- Documented account-gated slugs. `gemini-4-neon-low`, `gemini-4-neon-medium`, `gemini-4-neon-high`, `gemini-4-neon-xhigh`, `gemini-4-argon-high`, `gemini-pro-orchestrator-g1-pro`, and `claude-opus-5-5-high`.
- Policy exclusion. `gpt-oss-*` (such as `gpt-oss-120b-medium`) is strictly eliminated from all PStack catalogs, panels, role assignments, and override templates.
- November 30, 2026 deprecations. `Gemini 4 Argon`, `Gemini 3.8 Flash`, `GPT-OSS-120b`, and `Claude 4.6` (`claude-opus-4-6-thinking`, `claude-sonnet-4-6`) retire after `2026-11-30`. Migrate Neon/Argon seats to `gemini-4-neon-*`, fast seats to `gemini-4-hydrogen-low` or `gemini-4-neon-low`, and minimal specialist seats to `claude-opus-5-5-high` or `Claude Sonnet 5.5 (thinking)` once active on the account.

## Hooks, headless mode, ACP, and validation

- Hooks. Native Antigravity plugins place `hooks.json` directly at the plugin root. Hook matchers must match headless internal tool names (`view_file`, `replace_file_content`, `multi_replace_file_content`, `write_to_file`, `list_dir`, `find_by_name`, `grep_search`, `read_url_content`).
- Goals and scheduling. `/goal` intercepts session stops via `<!-- GOAL_COMPLETE -->` and `<!-- GOAL_CANCELLED -->` markers. Background timers and crons use `schedule` and `manage_task`.
- Headless and ACP. Scripted runs use `agy -p` with `--output-format` (`text`, `json`, `stream-json`), `--input-format stream-json`, `--json-schema`, and `--print-timeout`. Editor JSON-RPC integration runs via `agy acp`.
- Plugin validation. Validate packaged Antigravity plugins with `agy plugin validate --strict --json`, and verify live parity with `agy models` and `agy agents`. Keep root `plugin.json` canonical inside `~/.gemini/config/plugins/pstack` without stale `.antigravity-plugin/plugin.json` shadow copies.

## Skill precedence (`skill_order`)

PStack primaries take precedence over Antigravity builtins when both exist. Builtins fill gaps with no PStack command or serve as explicit fallback when PStack is absent.

| Need | Primary PStack | Antigravity Builtin |
| --- | --- | --- |
| Parallel fan-out swarm | `/swarm` | `/swarm` (gated) |
| Multi-agent teamwork | `/swarm` | `/teamwork` |
| Adversarial interrogation | `/interrogate` | `/grill-me` |
| Loop until completion predicate | `playbooks/autonomous-run.md` | `/goal` |
| Spec then plan | `null` | `/plan` |
| Schedule recurring or delayed check | `null` | `/schedule` |
| Temporary reasoning boost | `null` | `/boost` |
| Compact session context | `null` | `/compact` |
| Scripted multi-phase workflow | `null` | `/run-workflow` |
