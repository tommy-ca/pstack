# pstack in Claude Code

> [!WARNING]
> **Status: Non-validated harness reference / external adaptation guide.**
> Claude Code is maintained as an experimental adapter candidate in `profiles/claude.json` and `.claude-plugin/`, but is **not** a declared native host target in `pstack.package.json#host_targets` (which strictly spans the verified 6-harness matrix: `grok`, `codex`, `omp`, `opencode`, `antigravity`, `droid`). No live native spawn/join evidence, verified background loops, or CI proof are claimed here.

pstack skills use canonical, host-neutral definitions. In Claude Code, read this file once per session, then map canonical skills and subagents with the tables below. `<pstack>` means the directory that holds `skills/` and `docs/`. Never pass a field or value that the Claude Code tool schema rejects.

## Native vs Shim vs Gap Taxonomy

| Capability Plane | Classification | Operational Meaning in Claude Code |
| --- | --- | --- |
| **Skill Discovery** | Native | Discovers project-local skills in `.claude/skills/` and user-global skills in `~/.claude/skills/`. Standard markdown instruction parsing. |
| **Tool Execution** | Native | Standard execution via `Bash` (with `rg` fallback) and native file inspection (`Read`, `Edit`). |
| **Subagent Dispatch** | Shim | Mapped through Claude Code `Agent` tool (`subagent_type: "general-purpose"` or `"Explore"`). Bounded to depth 1 (parent-owned orchestration). |
| **Workspace Isolation** | Shim | Advisory isolation via branch checkouts or directory allowlisting. No kernel-level filesystem sandboxing or hard readonly mounts. |
| **Todo Tracking** | Shim | Host todo tracking tool if exposed by the session; otherwise formatted markdown status updates in chat reply. |
| **Background Scheduling** | Gap | Claude Code CLI has no native daemon scheduler, recurring cron, or monitor loops. Overnight or automated workflows require external process supervisors. |
| **Automations & Cloud VMs** | Gap | No Cursor Automations, webhook endpoints, Bugbot runtime, or remote cloud VMs. All commands run in the local environment. |

## Tools

| Canonical / Portable Concept | Claude Code Primitive | Notes |
| --- | --- | --- |
| `agent.spawn` / Subagent | `Agent` | Parent-owned dispatch; depth bounded to 1. |
| Human Question | `AskUserQuestion` | In `-p` / noninteractive mode it is absent, so ask in plain text and wait. |
| Todolist / State tracking | Host todo tool | Use if session offers it; otherwise maintain list in reply. |
| Run another pstack skill | `Read` `<pstack>/skills/<name>/SKILL.md` | Follow instructions directly. When instructing the user, suggest `/pstack:<name>`. |
| Code Search | `Bash` with `rg` | Standard grep fallback when session lacks search tools. |

## Subagent fields

| Canonical / Host Field | Claude Code Primitive | Notes |
| --- | --- | --- |
| `subagent_type: general-purpose` | `general-purpose` | Standard execution worker. |
| `subagent_type: "pstack:poteto-agent"` | `pstack:poteto-agent` | Canonical poteto-mode worker. |
| `subagent_type: "pstack:independent-verifier"` | `pstack:independent-verifier` | Independent verification worker. |
| `readonly: true` | `subagent_type: "Explore"` | Read-only exploration. Keeps `Bash`; brief must forbid writes. |
| `readonly: false` | `general-purpose` | Standard writer subagent. |
| `isolation: "worktree"` | `isolation: "worktree"` | Name checkout branch/commit in brief. |
| `environment: "local"` | Omit | Default local process execution. |
| `run_in_background: true` | Background task | Subagents run asynchronously and notify on completion. |
| `resume` | New agent spawn | Pass earlier context in brief. |
| `file_attachments` | List paths in brief | Claude Code CLI reads files from path citations. |

## Models and roles policy

Claude Code binds models via the active CLI model selection and the `pstack-models.md` rule.

| Role Category | Canonical pstack Mapping | Claude Code Value |
| --- | --- | --- |
| Heavy Reasoning (`pro`, `opus`) | `claude` candidate profile | `model: "opus"`, `effort: "high"` or `"xhigh"` |
| Standard Implementation (`flash`, `sonnet`) | Standard worker roles | `model: "sonnet"`, `effort: "medium"` or `"high"` |
| Fast / Exploration (`haiku`) | Read-only explorer / quick checks | `model: "haiku"`, `effort: "low"` |
| Non-Claude slugs (`grok-*`, `gpt-*`) | Host-neutral fallback | Omit model parameter to inherit parent session model. |
| `auto` or `inherit-parent` | Inherit parent session | Omit model parameter. |

### Roles configuration

Write model and reasoning effort mappings to `~/.claude/rules/pstack-models.md` or `.claude/rules/pstack-models.md`. Claude Code loads `.md` files in rules directories into session context.
Do not put role assignment lines into `CLAUDE.md` or shared skills.

## Unsupported features (fail-closed gaps)

When an execution playbook calls for features unavailable in Claude Code, fail closed and follow these explicit behaviors:

- **Cursor Automations:** No routine hooks, webhooks, or secret dispatch. Skip with explicit notice: `Skipped in Claude Code: <step>. Reason: no native automation runner.`
- **Bugbot:** Triage GitHub review comments via forge CLI (`gh pr view`). Do not claim Bugbot automated triggers.
- **Cloud VMs:** Run in local worktree branch (`isolation: "worktree"`). Do not attempt to provision remote VMs.
- **Daemon `/loop`:** Do not claim background loops. Report as manual operator cadence or external cron supervisor.
