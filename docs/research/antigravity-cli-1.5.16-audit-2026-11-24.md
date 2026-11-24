# Antigravity CLI 1.5.16 official feature and tool audit

**Date.** 2026-11-24
**Subject.** Google Antigravity CLI (`agy` 1.5.16) capabilities, tool surface, models, and PStack gaps.
**Linked Issue.** Epic #1436, Unit 1 (#1437).

## Observed local environment

The local `agy` binary at `/home/tommyk/.local/bin/agy` reports version `1.5.16`.
Installed built-in skills live under `/home/tommyk/.gemini/antigravity-cli/builtin/skills/`.
That directory ships 16 built-in skills, including `native_swarm`, `swarm_monitor`, `swarm_narrator`, `swarm_pane`, `run-workflow`, `agy-customizations`, `antigravity_guide`, `automation`, `conversations`, `generative_ui`, `mcp-app-development`, `migrate-agent-settings`, `migrate-workflows`, `permissioned-github`, `plugin`, and `ui-plugin-navigation`.

`agy models` reports the live account catalog on this machine.

- `gemini-4-hydrogen-high`, `gemini-4-hydrogen-xhigh`, `gemini-4-hydrogen-medium`, `gemini-4-hydrogen-low`
- `gemini-3.8-flash-high`, `gemini-3.8-flash-medium`, `gemini-3.8-flash-low`
- `claude-sonnet-4-6`, `claude-opus-4-6-thinking`
- `gpt-oss-120b-medium` (excluded by PStack policy)

`agy agents` discovers 25 subagents, consisting of the 22 PStack canonical roles plus 3 built-in `jd-*` Judgment Day agents (`jd-fix-agent`, `jd-judge-a`, `jd-judge-b`).

## Official documentation corpus

Official Markdown mirrors were retrieved from `https://antigravity.google/` via the index at `https://antigravity.google/llms.txt` and cross-checked against `agy --help`, `agy plugin --help`, and `agy changelog`.

- CLI Reference (`https://antigravity.google/docs/cli/reference.md`). Lists TUI slash commands (`/swarm`, `/swarm board`, `/run-workflow`, `/boost`, `/teamwork`, `/goal`, `/schedule`, `/grill-me`, `/plan`, `/agents`, `/tasks`, `/diff`, `/effort`, `/context`, `/compact`, `/fork`, `/rewind`, `/plugin`, `/hooks`, `/remote-control`, `/voice`), default keybindings (`Alt+S` swarm board, `Alt+X` dismiss swarm row, `Alt+J` jump to waiting subagent, `Ctrl+K` fast-approve subagent, `Shift+Tab` cycle execution mode), startup flags (`--mode`, `--model`, `--effort`, `--agent`, `--add-dir`, `-c`, `-r`/`--resume`/`--conversation`, `-p`/`--print`/`--prompt`, `--output-format`, `--input-format`, `--json-schema`, `--print-timeout`, `--disable-slash-commands`, `--sandbox`, `--dangerously-skip-permissions`, `--remote-control`, `--remote-agent`, `--project`, `--new-project`, `--settings`), and `~/.gemini/antigravity-cli/settings.json` keys.
- CLI Best Practices (`https://antigravity.google/docs/cli/best-practices.md`). Covers verification loops, explore-plan-execute, `AGENTS.md`/`GEMINI.md` rules, `auto` mode with terminal sandbox, `/rewind`, `/compact`, `/fork`, `-p` automation, and parallel background subagents.
- Swarm (`https://antigravity.google/docs/swarm.md`). Documents `/swarm` across all plans, coordinator board tools (`swarm`, `post_message`, `read_board`, `swarm_wait`), `@name`/`@group`/`@all`/`@#channel` addressing, `workspace` modes (`inherit`, `share`, `branch`), `fork`, `channels`, live status row, `/swarm board` TUI (`Alt+S`), `@monitor` (`swarm_monitor`), and `swarm_pane` (`plan.json` overview replacing `swarm_narrator`).
- Dynamic Workflows (`https://antigravity.google/docs/dynamic-workflows.md`). Documents `/run-workflow` Python scripts using `phase()`, `log()`, `agent()`, `parallel()`, `pipeline()`, `trajectory()`, `call_tool()`, `CONVERSATION_ID`, `STEP_INDEX`, and `WORKSPACES`, with structured JSON-Schema `finish` outputs and per-agent `workspace` (`inherit`, `branch`, `share`) and `model` (`inherit`, `flash_lite`, `flash`, `pro`).
- Custom Subagents (`https://antigravity.google/docs/subagents.md`). Documents `invoke_subagent`, `define_subagent`, `manage_subagents`, `send_message`, built-in `research`, `browser`, and `self` agents, Markdown agent discovery (`.agents/agents/`, `~/.gemini/config/agents/`, `plugins/<name>/agents/`), and the runtime nesting limit of 10 levels (while PStack enforces depth 1 by policy).
- Models and Orchestrator (`https://antigravity.google/docs/models.md`). Documents `Gemini 4 Neon` (`low`, `medium`, `high`, `xhigh`), `Gemini 4 Carbon`, `Gemini 4 Argon`, `Gemini 4 Hydrogen`, `Orchestrator` planner/executor pairing (`gemini-pro-orchestrator*` and `--model "Orchestrator (Neon|Carbon|Argon)"`), `Claude Sonnet 5.5 (thinking)`, `Claude Opus 5.5 (thinking)`, and the November 30, 2026 deprecation of `Gemini 4 Argon`, `Gemini 3.8 Flash`, `GPT-OSS-120b`, and `Claude 4.6`.
- Effort (`https://antigravity.google/docs/cli/commands/effort.md`). Documents `/effort [low|medium|high|xhigh|max]` and `--effort` overrides for adjustable models (fixed-budget `Orchestrator` excludes effort adjustment).
- Schedule and Goal (`https://antigravity.google/docs/commands/schedule.md`, `https://antigravity.google/docs/commands/goal.md`). Documents `schedule` (`DurationSeconds`, `Prompt`, `TimerCondition`, `CronExpression`, `MaxIterations`, `IsDaemon`, `ExactTiming`), `manage_task` (`list`, `status`, `send_input`, `kill`), and `/goal` stop-hook interception (`<!-- GOAL_COMPLETE -->`, `<!-- GOAL_CANCELLED -->`).
- Headless Mode and ACP (`https://antigravity.google/docs/cli/headless.md`, `https://antigravity.google/docs/cli/acp.md`). Documents `-p` (`text`, `json`, `stream-json`), `--input-format stream-json`, `--json-schema`, `--print-timeout`, exit codes, `agy models`, `agy agents`, and `agy acp` JSON-RPC editor integration.
- Plugins, Hooks, and Discovery (`https://antigravity.google/docs/plugins.md`, `https://antigravity.google/docs/hooks.md`, `https://antigravity.google/docs/customization-discovery.md`). Documents `agy plugin validate [--strict] [--json]`, `~/.agents/skills` global discovery (`1.5.16+`), `hooks.json` placement directly at plugin root for native plugins, and `settings.json` / `plugins.json` configuration.

## Tool surface findings

A live `agy -p ... --output-format stream-json --model gemini-3.8-flash-low` probe confirmed the headless and hook tool IDs emitted in `init.tools`.

- File tools in `init.tools` and `hooks.md` use `view_file`, `write_to_file`, `replace_file_content`, `multi_replace_file_content`, `list_dir`, `find_by_name`, `grep_search`, and `read_url_content`.
- Interactive CLI sessions on Gemini 4 Hydrogen expose model-facing aliases `read_file`, `edit_file`, `write_file`, `run_command`, `manage_task`, `schedule`, `invoke_subagent`, `define_subagent`, `manage_subagents`, `send_message`, `run_workflow`, `ask_question`, `search_web`, `call_mcp_tool`, `list_resources`, and `read_resource`, plus `swarm`, `post_message`, `read_board`, and `swarm_wait` when `/swarm` is active.
- `agy 1.5.13+` guards native `swarm` creation behind an explicit `/swarm` invocation or an active swarm board so agents do not spawn quota-heavy swarms unprompted.

## Current PStack gaps identified

1. `skills/setup-pstack/profiles/antigravity.json` and `skills/poteto-mode/references/antigravity-tools.md` omit native `swarm` (`swarm`, `post_message`, `read_board`, `swarm_wait`, `swarm_pane`, `swarm_monitor`) and `run_workflow` (`parallel`, `pipeline`, `phase`, `trajectory`).
2. `tool_mappings` in `profiles/antigravity.json` documents only legacy/internal file tool names without noting the interactive CLI aliases (`read_file`, `edit_file`, `write_file`) or the `1.5.13+` `/swarm` gate.
3. `.antigravity-plugin/models.json` and `scripts/package_projection.py` omit `gemini-4-neon-xhigh`, `gemini-4-neon-high`, `gemini-4-hydrogen-medium`, `gemini-4-hydrogen-low`, `claude-opus-4-6-thinking`, and `claude-sonnet-4-6` while pinning `claude-opus-5-5-high` which is absent from the local `agy models` catalog.
4. `scripts/drivers/antigravity.py` and `.agents/skills/verify-antigravity-pstack/` test only `agy plugin validate` (non-strict) and static file counts instead of exercising `agy plugin validate --strict --json`, `agy models`, `agy agents`, and the refreshed Antigravity tool and model contracts.
5. `~/.gemini/config/plugins/pstack` on disk contained a stale `.antigravity-plugin/plugin.json` (`0.15.29-preview.0`) alongside root `plugin.json` (`0.15.36-preview.0`) and drifted `technical-writing/SKILL.md`, causing `agy plugin list --json` to report `0.15.29-preview.0` and `sync_antigravity_plugin.py --check` to fail.
