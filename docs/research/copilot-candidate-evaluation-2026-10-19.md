# GitHub Copilot candidate adapter evaluation (issue #442, program #429)

Review and formal capability mapping of GitHub Copilot CLI and editor integrations against the pstack portability schema and host identity registry (#446). No code or policy forks; candidate profile and driver added under declared external host identity `github:copilot`.

---

## 1. Context and Seam Boundaries

Issue #442 evaluates GitHub Copilot as a candidate adapter under Sub-epic #432 (Native adapter, packaging and hook parity) of Program #429.

### Dependencies and Prerequisites
- **#440 (Projector + hooks)**: session lifecycle hook evaluation and honest negative gates landed on trunk in PR #575 (`ec0a1ab`).
- **#446 (Host identity registry)**: replaced the closed host enum with a centralized domain model (`scripts/host_identity.py` and `schemas/portability/host-id.schema.json`). Under #446:
  - `BUILTIN_HOSTS = ("grok", "codex", "omp", "opencode", "antigravity", "droid")` remains strictly closed to the six built-in hosts.
  - Declared external hosts must be namespaced: `<namespace>:<name>` matching `EXTERNAL_HOST_ID_PATTERN`.
  - Bare names (such as unnamespaced `copilot`) are explicitly refused to prevent uncoordinated collisions with the flat built-in namespace.
  - Declared hosts start at `support_state: "candidate"`, and all bindings must remain `static-only` until proven by host-scoped live receipts.

---

## 2. Reference Copilot Architecture and Surfaces

GitHub Copilot manifests across three distinct operational surfaces with divergent capability profiles:

| Surface | Execution Model | Tooling / Subagent Dispatch | Isolation / Permissions |
| --- | --- | --- | --- |
| **Copilot CLI** (`gh copilot` / standalone CLI) | Interactive terminal shell assistant (`suggest`, `explain`) | Single-process REPL; no subagent dispatch primitive; shell command execution via user confirmation | Unsandboxed terminal cwd; no container/overlayfs mount isolation |
| **Copilot in IDE** (VS Code, JetBrains) | Editor extension with inline completions and Chat panel (`@workspace`, `/explain`, `/fix`) | Chat participants and tools via VS Code Language Model API; no autonomous background child spawn | Host IDE workspace trust; file access subject to editor workspace permissions |
| **Copilot Extensions / Workspace** | Cloud-based GitHub App service communicating via Server-Sent Events (SSE) | Agent-like webhook integration; centralized GitHub API routing; external cloud execution | Ephemeral cloud containers managed by GitHub; outside local developer workspace |

To avoid policy forks or false claims of multi-agent parity, pstack targets the **local developer environment (CLI and workspace)** as the candidate execution surface.

---

## 3. Capability Mapping Across PORTABLE_CAPABILITY_UNIVERSE

Every portable capability in `PORTABLE_CAPABILITY_UNIVERSE` (17 capabilities) is classified below with settlement strength and rationale:

| Capability | Implementation Status | Enforcement | Verification Status | Primitive | Notes |
| --- | --- | --- | --- | --- | --- |
| `agent.spawn` | **gap** | advisory | static-only | `none` | Copilot CLI operates in single-process interactive mode; no autonomous subagent spawn primitive exists. |
| `agent.join` | **gap** | advisory | static-only | `none` | No child subagent completion or join primitive. |
| `agent.cancel` | **gap** | advisory | static-only | `none` | No subagent process cancellation primitive. |
| `agent.message` | **gap** | advisory | static-only | `none` | No inter-agent communication or steering primitive. |
| `agent.resume` | **gap** | advisory | static-only | `none` | No child session resumption primitive. |
| `workspace.shared` | **native** | hard | static-only | `working directory (cwd)` | Commands and file inspections run in current repository workspace. |
| `workspace.isolated` | **gap** | advisory | static-only | `none` | Copilot CLI provides no container, overlayfs, or native worktree isolation mount. |
| `workspace.readonly` | **native** | advisory | static-only | `prompt instruction (read-only posture advice)` | Prompt-level read-only posture advice. Copilot exposes no kernel-level read-only mount. |
| `human.ask` | **native** | hard | static-only | `interactive terminal confirmation` | Interactive dialog prompting user in terminal. |
| `human.gate` | **native** | hard | static-only | `blocking terminal execution confirmation` | Blocking confirmation before executing proposed commands. |
| `plan.update` | **native** | hard | static-only | `todo markdown (logbook tracking in repository)` | Markdown logbook and task tracking in repository files. |
| `schedule` | **gap** | advisory | static-only | `none` | No native cron or timer scheduler primitive. |
| `monitor` | **gap** | advisory | static-only | `none` | No background process monitoring primitive. |
| `session.persist` | **native** | advisory | static-only | `shell history (terminal session history)` | Terminal history preserves command logs; no structured session database. |
| `session.resume` | **gap** | advisory | static-only | `none` | No structured session restoration primitive. |
| `evidence.capture` | **native** | hard | static-only | `evidence ledger (.audit/evidence/)` | Repository evidence ledger files. |
| `verify` | **native** | hard | static-only | `copilot verification checks` | Verification driver checks and schema validation. |

---

## 4. Key Architectural Decisions

### 4.1 No Unsupported Default Model
GitHub Copilot model routing is controlled by the GitHub Copilot backend proxy (`api.githubcopilot.com`), which exposes model families like GPT-4o, Claude 3.5 Sonnet, and o1 based on organizational policy and user tier.

In `profiles/copilot.json`:
- `runtime_conventions.default_model` is strictly `"inherit"`.
- `runtime_conventions.forbidden_spawn_fields` explicitly forbids `"model"` and `"effort"` overrides.
- No custom model slugs are hardcoded, preventing policy forks or runtime failures on unentitled models.

### 4.2 Multi-Agent Dispatch Stays GAP
Unlike Anthropic Claude Code (which provides a native `Task` tool for depth-1 subagent dispatch) or OMP (which provides a native `task` tool over RPC), GitHub Copilot CLI does not expose any subagent dispatch mechanism.

Attempting to simulate subagent spawn via shell backgrounding (`&`) or subshells would violate the pstack portability contract. Therefore:
- `agent.spawn`, `agent.join`, `agent.cancel`, `agent.message`, and `agent.resume` are explicitly mapped as `implementation_status: "gap"`.
- `runtime_conventions.forbidden_spawn_fields` includes `"subagent_type"`.

### 4.3 Filesystem Isolation and Read-Only Posture
Copilot CLI runs directly on the host machine in the current working directory.
- `supported_isolation_modes` is strictly `["none"]`.
- `workspace.readonly` is explicitly categorized as `enforcement: "advisory"`. Consistent with `test_binding_rejects_prompt_only_as_hard_enforcement`, attempting to claim `enforcement: "hard"` for prompt-based read-only postures is rejected fail-closed with `ValidationError`.

### 4.4 Hook Lifecycle and Context Injection
Copilot CLI does not support executable lifecycle hooks (e.g. `SessionStart`, `PrePrompt`).
Contextual guidelines are provided through repository documentation files:
- `.github/copilot-instructions.md` for workspace-wide behavioral instructions.
- Skills discovered from `.github/skills/` or `.copilot/skills/`.

---

## 5. Settlement Strength and Promotion Gate

GitHub Copilot candidate integration is delivered with:
- Profile: `profiles/copilot.json` with `host: "github:copilot"`, `support_state: "candidate"`.
- Driver: `scripts/drivers/copilot.py` implementing `CopilotDriver(HarnessDriver)`.
- Verification: `tests/test_copilot_driver.py` covering schema conformance, declared host gates, fail-closed negative gates, and driver scenarios.

Per the pstack durability contract, `github:copilot` cannot be promoted to `packaged` or `supported` without an immutable, host-scoped live receipt generated by an authenticated Copilot CLI runtime. Status remains `candidate` with `evidence_level: static-only`.
