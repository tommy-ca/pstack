# Droid tool mapping for pstack

This document maps portable pstack capabilities to Factory Droid native
primitives and conventions. Verified against Droid CLI 0.233.0 offline
surfaces. Model-backed behavior is explicitly untested: offline checks never
prove skill serving, model selection, or spawn execution.

## Tool actions

| Portable Capability | Droid Native | Notes |
| --- | --- | --- |
| Read / search | `Read`, `Grep`, `Glob`, `LS` | |
| Edit / write | `Edit`, `Create` | |
| Shell | `Execute` | |
| Fetch / web search | `FetchUrl`, `WebSearch` | |
| `plan.update` | `todo_write` | Always included in every droid. |
| `agent.spawn` | `Task` (`subagent_type`, `description`, `prompt`) | Parent-owned. Optional fields come from the live session schema (`await`, `complexity`, `resume`, `image_paths`); check the schema in the running session, not docs. |
| `agent.join` | `TaskOutput` (`block=true` waits) | Background reports auto-deliver. |
| `agent.cancel` | `TaskStop` | SIGTERM, then SIGKILL. |
| `agent.message` | `Task` with `resume` | Full child context preserved. |

## Spawn contract

- Required fields are always `subagent_type`, `description`, `prompt`.
- There are no per-spawn `readonly`, `isolation`, `cwd`, `model`,
  `reasoning_effort`, or `environment` fields. Sending them is the error.
- Read-only posture is a per-droid-definition `tools` restriction
  (omit the field for all tools). **Namespace caveat:** the `tools:` value
  namespace is load-time-untested (see "Explicitly untested"). Two different
  tool taxonomies are observed offline and must not be conflated:
  `droid exec --list-tools -o json` on CLI 0.233.0 reports 30 tools under
  `category` values `read`/`edit`/`execute` (the `execute` category has 12
  members including the Task family and automation tools; the only
  `edit`-category llmId is `ApplyPatch`), while the live session surface
  exposes tools named `Edit` and `Create` that the inventory does not list.
  The category-expansion claims below came from error-surface observation
  during review, not from load-time acceptance.
- The frontmatter parser splits comma-separated scalars but does not strip
  bracket characters, so list IDs comma-separated (`tools: Read, Grep,
  Glob, LS, Execute`), never bracket-wrapped. `tools: all` is not a valid
  member list. The shipped union IDs are all llmIds present in the offline
  inventory.
- Depth is hard-fixed at 1: children cannot spawn children. Spawning is
  parent-owned.
- Worktrees are session-level (`droid -w`); per-spawn isolation does not
  exist.

## Droid definitions (`droids/*.md`)

- `name` uses the hyphenated `pstack-<role>` spelling. Colons are invalid.
- `model: inherit` resolves to the parent session model. No effort override:
  inherited models ignore `reasoningEffort`, and the shipped Grok `xhigh`
  ladder tier has no Droid equivalent.
- Grok `capabilityMode: execute` grants read + shell, but the per-spawn
  model/effort surface does not exist, so execute-mode pstack droids pin the
  union explicitly: `tools: Read, Grep, Glob, LS, Execute` (comma-separated
  scalar, no file-edit IDs). Grok
  `inheritSkills: false` has no Droid equivalent, so plugin droids keep skill
  access and the parent prompt owns skill discipline.
- The Droid builtin general-purpose subagent type observed in a live
  session's subagent catalog is `worker` (used where Grok roles said
  `general-purpose`).

## Skill precedence (inverted vs pstack-first hosts)

Folder and project skills outrank project plugin skills; personal skills
outrank user plugin skills; a user skill with the same name shadows the pstack
plugin skill. The pstack skill-order table is advisory here; the platform
precedence above is the hard layer.

## Scheduling

No in-session scheduler primitive exists. Recurring work uses the Automations
platform surface, not a session tool.

## Offline checks (no model call)

- `droid doctor --config --json` validates installed skill frontmatter and
  reports `configuration.skill-invalid` findings.
- `droid exec --list-tools -o json` lists the tool surface, including
  `task-cli`, `task-output-cli`, `task-stop-cli`, and `todo_write`.
- Plugin identity is the marketplace entry plus the registered marketplace
  name. `.factory-plugin/plugin.json` fields are a metadata convention that
  Droid does not read.
- There is no `droid inspect`, no `droid plugin validate`, and no
  enable/disable command.

## Explicitly untested

Custom-role serving, model selection, droid-file load-time acceptance, and
actual `Task` spawn/join/cancel behavior need a live model-backed session.
Offline validation never proves them.
