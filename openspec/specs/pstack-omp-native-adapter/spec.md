# pstack-omp-native-adapter Specification

## Purpose
Native OMP host adapter: discovery precedence, role/model resolution, package installation and lifecycle, workspace safety, and evidence-based conformance at a pinned OMP revision.

## Requirements

### Requirement: canonical authority and boundary
The OMP adapter MUST preserve canonical `cursor/plugins/pstack` principles and playbook semantics. It MUST not copy Grok-specific settings, `spawn_subagent` wire aliases or runtime models into canonical OMP bindings. Every capability MUST be recorded with OMP version/commit, implementability and evidence strength. All normative binding changes require links to native OMP docs or code at pinned revision.

#### Scenario: pstack upstream changes

- **GIVEN** a new canonical pstack revision is available
- **WHEN** the portable pin and OMP projection are updated
- **THEN** canonical drift is classified independently of OMP adapter parity
- **AND** shared principles and playbook behavior remain upstream-owned

### Requirement: first-class native package
The OMP package MUST be loadable by a documented OMP discovery path using conventional `skills/<name>/SKILL.md`, required `agents/<name>.md` for every portable role used by a playbook, and a valid OMP-recognized package manifest where plugins are used. Existing `scripts/package-lifecycle.py::install_plugin(host='omp')` copies skills, agents (#299), and a generated `plugin.json`; the adapter MUST test native role discovery on the installed package rather than infer it from shared repo files. It MUST NOT rely solely on `.omp-plugin/plugin.json` unless its native loader support is independently proven. An extension `ExtensionAPI` shim MUST NOT be created unless native skills/agents cannot meet a specific tested requirement.

#### Scenario: clean install, collision and removal

- **GIVEN** a clean isolated OMP user/project configuration
- **WHEN** the package is linked or installed and an existing skill name collides
- **THEN** the installed package's named skills and task agents are discoverable with source attribution
- **AND** update, disable, uninstall, and namespace handling preserve user-created files

### Requirement: OMP-native role and model routing
Agents MUST be generated from portable role definitions into OMP-discoverable agent files with valid frontmatter. OMP `modelRoles` maps role names to user-chosen selectors; configuration MUST NOT overwrite providers, credentials or user-scoped settings. The adapter SHOULD test precedence of project/user/extension agent definitions.

#### Scenario: model alias

- **GIVEN** an OMP task agent specifies `model: "@review"` and the role is configured
- **WHEN** the reviewer is actually dispatched
- **THEN** the receipt records the observed resolved model or a BLOCKED prerequisite
- **AND** provider credentials and existing user model settings are not overwritten

### Requirement: truthful native runtime proof
`scripts/drivers/omp.py` MUST distinguish static/offline from live, and MUST NOT report runtime PASS based on profile matching, `--help` string matching, `omp plugin list` alone, or receipt existence. Live agent proof MUST observe spawned child identity, result or error, join, bounded timeout, cleanup and exact revision. Missing binary/provider or unmet prerequisites MUST be BLOCKED/UNTESTED, not PASS.

#### Scenario: invalid old receipt

- **GIVEN** a historical receipt records overall PASS while only profile/static checks ran
- **WHEN** the verifier derives its current OMP support state
- **THEN** the historical receipt cannot qualify as model-backed live execution
- **AND** invalidation and evidence levels are reported explicitly

### Requirement: independent orchestration
Swarm MUST use independent slices, join and evidence aggregation. Arena MUST freeze a rubric and isolate candidate writers before synthesis and lever verification. Interrogate MUST use independent reviewers with no write capability and aggregate disagreements. OMP WorkPool MAY optimize eligible fan-out; where it reuses a context it MUST NOT count as fresh independent review. Distinct task/eval dispatch paths MUST be tested before mapped as interchangeable.

#### Scenario: reused context

- **GIVEN** WorkPool reuses a keep-alive worker from a previous item
- **WHEN** Arena or Interrogate requires a fresh independent review
- **THEN** the adapter selects a truly fresh reviewer context or reports a gap
- **AND** the reused context is not counted as an independent judge

### Requirement: workspace safety and session semantics
An isolated writer MUST not mutate the parent checkout before a reviewed apply/merge gate; replay must verify post-cleanup residue. Read-only MUST be called advisory unless write-denial is enforced. Parent session resume MUST be separate from child agent resume, and eval kernel state MUST NOT be assumed to persist after cold restart. Scheduling stays `gap` until durable native evidence exists.

#### Scenario: write and resume

- **GIVEN** an isolated worker and a parent-checkout sentinel exist
- **WHEN** the worker completes or is cancelled and an OMP parent session is resumed cold
- **THEN** the original sentinel remains untouched and worktree cleanup is accounted for
- **AND** parent session restoration is not mislabeled child-agent handle revival

### Requirement: explicit canonical Orchestrate parity classification
The OMP adapter MUST distinguish the current portable `orchestrate` flat-coordinator implementation (one coordinator, direct workers, depth policy 1) from upstream Cursor pstack's nested coordinator/track workflow. Because these differ semantically, the adapter MUST record upstream Orchestrate nested-coordinator behavior as `adapted` or `gap` until source- and live-proof-backed equivalence exists. OMP's native recursion default MUST NOT be asserted as an enforced pstack policy. The adapter MUST not construct a second durable scheduler to simulate unsupported nested tracks.

#### Scenario: multi-level coordinator request

- **GIVEN** an upstream playbook requires coordinator, sub-coordinator and worker levels
- **WHEN** the installed OMP adapter only supports the flat-coordinator policy
- **THEN** the run declares the adapted behavior or reports a gap
- **AND** full nested parity is withheld pending native ownership, depth and join evidence

### Requirement: evidence vocabulary and verifiable support-state derivation
The adapter MUST reuse the existing `schemas/portability/receipt.schema.json` evidence vocabulary (`static`, `offline`, `observed_live`, `legacy`) and verdict vocabulary (`PASS`, `FAIL`, `BLOCKED`, `UNTESTED`). `documented` is capability provenance, NOT a receipt evidence level. The adapter MUST NOT serialize invented `live` or `documented` evidence_level values. An `observed_live` claim MUST include actual target OMP invocation, model-backed child identification, terminal outcome and exact host/profile/package/driver provenance; historical `legacy` never automatically upgrades. Any severity aggregation MUST ensure FAIL takes precedence over BLOCKED/UNTESTED/PASS, and any BLOCKED/UNTESTED mandatory live requirement prevents support promotion.

#### Scenario: historical and mixed-severity receipts
- **GIVEN** a legacy OMP receipt that reports runtime PASS from static profile checks and a current result set containing FAIL and BLOCKED
- **WHEN** the verifier computes evidence strength and aggregate status
- **THEN** the legacy record is not promoted to observed_live and the current known failure is retained as FAIL
- **AND** the serialized receipt validates against the existing portability receipt JSON Schema without introducing new enums

### Requirement: bounded OMP RPC/SDK transport proof
The OMP integration driver MUST choose and report its transport (`rpc`, `sdk`, `cli`) with its host revision and isolated test profile. A preferred RPC probe MUST consume the `ready` frame, negotiate a compatible protocol version where needed, correlate commands by `id`, distinguish `prompt` admission response from terminal `prompt_result`, and wait for the correct `session_settled` / subagent terminal conditions when background work is relevant. A prompt acknowledgement or `agent_end` event alone MUST NOT prove that all child work settled. RPC `get_subagents`, `get_subagent_messages`, `cancel_subagent`, and `steer_subagent` MAY be used where supported by the pinned host. SDK probes MUST explicitly own and dispose their `AgentSession` and select file-backed versus in-memory persistence intentionally. A CLI `-p` smoke MUST NOT be treated as a substitute for subagent lineage proof.

#### Scenario: acknowledged prompt with unfinished subagent
- **GIVEN** OMP RPC accepts a `prompt` with a correlated `id` and launches a background subagent
- **WHEN** the adapter receives an admission acknowledgement and a `prompt_result` reporting `sessionSettled: false`
- **THEN** runtime execution is not marked complete until the agent/subagent terminal evidence or a bounded failure state is observed
- **AND** the receipt records the prompt identifier, selected transport, observed child IDs, terminal result, cleanup, and runtime configuration

#### Scenario: unavailable model or hanging transport
- **GIVEN** a missing model credential, unavailable native executable, rejected protocol negotiation, or a prompt that does not settle
- **WHEN** the bounded integration probe reaches its configured failure or deadline
- **THEN** it emits FAIL for an observed execution failure or BLOCKED/UNTESTED for an unmet prerequisite, never an invented PASS
- **AND** subprocess/process-group and subagent cleanup are attempted and reported without exposing secrets

### Requirement: execution-mode and provider-scope fidelity
OMP-native discovery, model role selection, read-only limitations, background jobs, session restoration and isolation MUST be verified for the selected execution mode and profile, not presumed transferable across interactive CLI, headless print, RPC and SDK. RPC/ACP protocol defaults may differ from interactive defaults. The adapter MUST explicitly record effective `task` and async policy, including recursion, concurrency, isolation and apply/merge. OMP `agent()` MUST resolve a selected agent's frontmatter and `modelRoles`; it MUST NOT pass a nonexistent per-call `model` option. Tests MUST use an isolated OMP `--profile` or equivalent explicit settings, without modifying a real user's credentials or home state.

#### Scenario: conflicting RPC isolation default
- **GIVEN** the interactive configuration requests worktree isolation but the RPC invocation uses protocol-specific defaults
- **WHEN** a pstack writer is spawned through RPC
- **THEN** the effective worktree and apply/merge policy are observed in the running mode and parent-checkout invariants are tested
- **AND** the interactive configuration alone cannot satisfy the RPC workspace-isolation requirement

### Requirement: scope, collision and package origin safety
The native OMP package MUST distinguish an installed npm/link plugin discovered via `package.json#omp` from project `.omp/skills` and user `.omp/agent/skills`; it MUST verify which provider owns a resolved skill/agent. Project and user precedence, skill namespacing, duplicate suppression and explicit plugin disable MUST be included in deterministic negative tests. `omp plugin link` may replace an existing target link and therefore MUST operate only in a disposable profile/install root; install/uninstall MUST leave foreign files, symlinks, host overrides and credentials unchanged.

#### Scenario: shadowed pstack router skill
- **GIVEN** a user-authored skill named `poteto-mode` collides with the installed pstack plugin skill
- **WHEN** the adapter resolves the canonical pstack router
- **THEN** the selected skill origin, optional namespaced alias and collision resolution are inspected rather than inferred from filename existence
- **AND** uninstall or disable does not delete or silently replace the user-authored skill

### Requirement: acceptance ladder
OMP support levels MUST be derived from revision-bound canonical, adapter, package and runtime receipts: `candidate -> mapped -> packaged -> verified -> supported`. All unsupported optional capabilities MUST be listed and scoped. The support claim MUST not exceed the weakest mandatory proof plane.

#### Scenario: partial evidence

- **GIVEN** canonical, adapter and package checks pass but a live child has not been exercised
- **WHEN** the adapter's support state is derived
- **THEN** the state is at most packaged for mandatory live capabilities
- **AND** the acceptance report identifies the missing native proof or prerequisites
