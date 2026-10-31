# pstack-portability Specification

## Purpose

Define the smallest portable contract that preserves canonical pstack intent across agent harnesses without introducing a second workflow runtime.

Official `cursor/plugins/pstack` at the immutable `UPSTREAM` pin is the canonical source. This repository is a reference port. Grok Build is the strongest reference adapter in this tree; Codex and Claude Code have mapping/packaging surfaces whose runtime support must be proven separately.

## Requirements

### Requirement: Canonical intent is upstream-owned

Feature: pstack-portability

Principles, skills, router behavior, playbook intent, roles, ordering, and verification rules MUST derive from the pinned official pstack tree. A host adapter MUST NOT become an intermediate source of truth for another host.

A port MUST track two independent states:

- `pin_conformance`: whether the port covers the immutable canonical pin.
- `upstream_freshness`: whether newer canonical changes remain unclassified.

A port MAY pass pin conformance while reporting upstream drift.

#### Scenario: reference port is not canonical

- **GIVEN** this repository
- **WHEN** portability behavior is reviewed
- **THEN** official pstack at `UPSTREAM` is the canonical authority
- **AND** this repository is reference evidence for host adaptation
- **AND** Codex, Claude Code, or future adapters do not normatively derive from the Grok mapping

### Requirement: Portable core stays small

The portable core MUST consist of canonical principles, skills, playbook intent, router semantics, roles, verification contracts, and the following host-bound semantic capabilities:

```text
agent.spawn
agent.join
agent.message
agent.cancel
agent.resume

workspace.shared
workspace.isolated
workspace.readonly

human.ask
human.gate
plan.update

schedule
monitor
session.persist
session.resume

evidence.capture
verify
```

The portability layer MUST NOT introduce a generic scheduler, task database, session manager, workflow DSL, provider gateway, or orchestration runtime when the host already owns those concerns.

#### Scenario: new harness

- **GIVEN** a new agent harness
- **WHEN** pstack is ported to it
- **THEN** the porter maps the semantic capabilities to native primitives, shims, version-gated behavior, or explicit gaps
- **AND** canonical playbooks are not rewritten as a new workflow language

### Requirement: Adapter bindings are typed and evidence-backed

A harness adapter MUST classify each required capability with:

```yaml
implementation_status: native | shim | version-gated | gap
enforcement: hard | soft | advisory
verification_status: verified | static-only | unverified | stale
```

A documentation or source-code observation MAY establish `static-only`. A claim about live host behavior requires runtime evidence before it is `verified`.

A prompt-only "do not write" posture is advisory and MUST NOT be reported as hard read-only enforcement.

#### Scenario: weaker substitute

- **GIVEN** a playbook requires hard isolation or read-only behavior
- **WHEN** the host offers only a prompt convention
- **THEN** the binding records the weaker enforcement strength
- **AND** the adapter does not claim semantic equivalence silently

### Requirement: Harness tool mappings are structured and schema-validated

Each harness adapter profile MUST declare a typed `tool_mappings` object conforming to `schemas/portability/tool-mapping.schema.json`.

The tool mapping defines explicit host primitives for file operations (`file_read`, `file_edit`, `file_write`), command execution (`shell_run`), network operations (`web_fetch`, `web_search`), subagent operations (`agent_spawn`, `agent_fanout`, `agent_join`, `agent_message`), background tasks (`task_background`), tool protocols (`tool_mcp`), plan updates (`plan_update`), and human questions (`human_ask`).

Upstream pstack skills MUST NOT be modified to hardcode host-specific execution commands. Primitives are resolved dynamically from the active harness profile.

#### Scenario: tool mapping validation
- **GIVEN** a harness profile in `profiles/`
- **WHEN** portability verification executes
- **THEN** the profile's `tool_mappings` object validates against `schemas/portability/tool-mapping.schema.json`
- **AND** missing or unmapped required capabilities fail the adapter gate

### Requirement: Harness runtime conventions are structured and schema-validated

Each harness adapter profile MUST declare a typed `runtime_conventions` object conforming to `schemas/portability/runtime-conventions.schema.json`.

The runtime conventions define maximum subagent depth (`max_subagent_depth`), supported workspace isolation modes (`supported_isolation_modes`), default model slug (`default_model`), allowed model-facing spawn fields (`allowed_spawn_fields`), forbidden spawn fields (`forbidden_spawn_fields`), and optional wire aliases (`wire_aliases`).

#### Scenario: runtime convention validation
- **GIVEN** a harness profile in `profiles/`
- **WHEN** portability verification executes
- **THEN** `runtime_conventions` validates against `schemas/portability/runtime-conventions.schema.json`
- **AND** subagent recursion depth exceeding the configured maximum is rejected

### Requirement: Skill order resolution follows a declared 3-tier fallback matrix

Each harness adapter profile MUST declare an ordered `skill_order` list conforming to `schemas/portability/skill-order.schema.json`.

For each capability need, resolution follows three strict tiers:
1. Primary pstack skill or playbook.
2. Secondary user skill fallback when primary pstack is not loaded.
3. Third-tier host bundled or builtin fallback.

Upstream skills MUST NOT contain hardcoded host branching. The skill order matrix defines deterministic fallback behavior.

#### Scenario: skill fallback resolution
- **GIVEN** a user request for a capability need
- **WHEN** the primary pstack skill is not active
- **THEN** the harness resolves the secondary user skill
- **AND** falls back to host builtin primitives only when secondary is absent

### Requirement: Canonical coverage is discovered, not counted

Portability verification MUST enumerate principles, playbooks, and relevant skills from the pinned canonical tree. Generic portability specs and tests MUST NOT encode literal inventory counts as the source of truth.

Every relevant canonical artifact MUST be classified as:

```text
preserve
adapt
exclude
gap
```

An `exclude` record MUST name a reason class such as packaging, host-specific, domain-pack, or policy.

#### Scenario: canonical adds an artifact

- **GIVEN** a new canonical pin contains an added principle, playbook, or skill
- **WHEN** the coverage lever runs
- **THEN** the artifact appears unclassified until the port records preserve, adapt, exclude, or gap
- **AND** a stale hardcoded count cannot hide it

### Requirement: Durable orchestration state remains host-owned

Playbooks MUST use the host's canonical task, agent, scheduler, session, and persistence state where those concepts exist. pstack MUST NOT create a competing durable orchestration store merely to erase a host gap.

Conceptual durable state includes work units, owners, claims, frontier, verification, gates, decisions, and retry state.

#### Scenario: host lacks durable field

- **GIVEN** a playbook needs durable state the host cannot represent
- **WHEN** the adapter executes that playbook
- **THEN** it records an explicit gate or gap
- **AND** it does not add a parallel pstack database by default

### Requirement: Swarm is a composition, not a harness primitive

The `swarm` skill MUST preserve this semantic shape:

```text
frame -> fan-out -> join -> evidence validation -> aggregate -> report
```

Workers MUST receive independent slices or explicitly declared race arms. Each brief MUST name goal, scope, verification method, and output contract. Missing or invalid worker evidence becomes a dropout or gap; a gap does not count as PASS.

Required host capabilities are `agent.spawn` and `agent.join`. Workspace isolation is required when workers write overlapping-risk state.

#### Scenario: host cannot parallelize

- **GIVEN** a swarm whose independence is required
- **WHEN** the host cannot create independent child contexts
- **THEN** the adapter reports a gap
- **AND** sequential reasoning in one context is not labeled equivalent

### Requirement: Arena is independent generation plus synthesis

The `arena` skill MUST preserve:

```text
frame rubric -> independent candidates -> cross-judge -> pick base -> graft -> verify
```

The rubric MUST exist before candidates run. Candidate writes MUST be separated. The synthesized artifact MUST be verified after grafting. Arena requires no special host API beyond ordinary spawn/join and, when writers are involved, workspace isolation.

#### Scenario: arena requires prior rubric and isolated writes

- **GIVEN** an arena run with N candidates
- **WHEN** candidates are spawned
- **THEN** each candidate writes to an isolated workspace
- **AND** the cross-judge scores against a pre-declared rubric
- **AND** the synthesized artifact is verified before acceptance

### Requirement: Interrogate is independent adversarial review

The `interrogate` skill MUST preserve independent reviewer contexts, a shared review contract, aggregation of consensus and disagreement, deduplication, and lead judgment. Reviewers MUST NOT auto-apply changes.

Model diversity is a useful adapter choice, not a portable semantic requirement.

#### Scenario: interrogate prevents auto-mutation

- **GIVEN** an interrogate review panel with diverse reviewers
- **WHEN** reviewers return findings
- **THEN** the reviewers do not auto-apply code edits
- **AND** the lead reviewer synthesizes findings into act on, consider, noted, or dismissed

### Requirement: Lever verification is the preferred proof pattern

The combination of **Build the Lever**, **Prove It Works**, and `create-verification-skill` defines the portable verification pattern. The port MUST prefer a deterministic lever over hand repetition.

For non-trivial work, the adapter MUST prefer the smallest rerunnable script, codemod, generator, skill, or driver that does or proves the work. When a project lacks a proof surface, the verification skill SHOULD expose:

```text
Launch
Doctor
Drive
Proof Bar
Evidence
Cleanup
```

with a maintained feature map.

A deterministic lever SHOULD be preferred over subagent fan-out when it can cover the work in one reliable pass.

#### Scenario: completion claim

- **GIVEN** an implementation is declared done
- **WHEN** verification is available on the real artifact
- **THEN** the verifier drives that artifact and records evidence
- **AND** compilation, static checks, or child self-report alone do not substitute for runtime proof

### Requirement: Supported harness is a proven state

A harness MUST transition through explicit lifecycle states:

```text
candidate -> mapped -> packaged -> verified -> supported
```

A harness is `supported` only when it has an adapter profile, an installation/packaging path where needed, static conformance, and runtime conformance for its required capabilities.

A mapping document alone is not support.

#### Scenario: partial adapter

- **GIVEN** a Codex or Claude mapping exists
- **WHEN** no runtime conformance evidence is recorded
- **THEN** the harness remains mapped or packaged
- **AND** documentation does not call it supported

### Requirement: Verification has three planes
The port MUST separate three **conceptual** conformance concerns: canonical pin/inventory/drift, adapter/native projection, and runtime observed behavior. For the existing serialized verification receipt, these concerns MUST map to the **four required and separately verdict-bearing** `canonical`, `adapter`, `package`, `runtime` planes in `schemas/portability/receipt.schema.json`. The `package` plane audits host-native manifest generation, install/link/discovery and lifecycle independently of adapter binding validation and runtime child execution. A positive result in one serialized plane MUST NOT substitute for an absent mandatory result in another. The distinction MUST be documented in the verifier without changing the existing receipt schema or creating a fifth plane.

#### Scenario: three plane separation
- **GIVEN** canonical, adapter, and runtime verification checks
- **WHEN** adapter static checks pass but runtime checks fail
- **THEN** runtime conformance reports FAIL
- **AND** static adapter PASS cannot be used to declare the harness supported

#### Scenario: three concerns, four receipt fields
- **GIVEN** a mapped OMP profile with passing static adapter checks and a missing installed `agents/` projection
- **WHEN** the four-plane receipt is computed
- **THEN** `adapter` MAY pass while `package` reports an independent failure or blocked status
- **AND** `runtime` cannot be declared observed-live PASS merely from the adapter outcome
- **AND** the output validates against the existing four-key receipt schema

### Requirement: Port architecture follows pstack principles

Portability changes MUST apply these design constraints:

- **Laziness Protocol**: smallest adapter and schema that preserve behavior.
- **Model the Domain**: explicit capability, binding, evidence, adaptation, and gap types.
- **Boundary Discipline**: host syntax stops at the adapter.
- **Build the Lever**: automate canonical indexing, drift classification, and conformance.
- **Prove It Works**: runtime claims require runtime proof.
- **Separate Before Serializing Shared State**: isolate writers before adding coordination.
- **Encode Lessons in Structure**: repeated port rules become checks or schemas.
- SOLID, KISS, DRY, and YAGNI constrain implementation.

#### Scenario: boundary enforcement

- **GIVEN** a new host adapter implementation
- **WHEN** host-specific configuration or syntax is processed
- **THEN** host primitives stop at the adapter boundary
- **AND** canonical playbooks remain host-neutral

### Requirement: Pilot reconciliation precedes scale

Contract differences discovered during the pilot harness MUST be reconciled and documented before scaling to secondary harnesses.

The pilot reconciliation MUST:
1. Reconcile tool mapping to portable capabilities rather than reference host call sites.
2. Enforce RFC 2119 separation between package descriptors and runtime orchestration.
3. Validate deterministic projection of native manifests.
4. Distinguish between global portability requirements and harness-specific compatibility utilities.

#### Scenario: pilot reconciliation gate

- **GIVEN** a completed pilot implementation for Codex
- **WHEN** scaling to OMP or OpenCode
- **THEN** the portability contract is reconciled against observed pilot evidence
- **AND** secondary harnesses build directly on the reconciled contract

### Requirement: Canonical semantic decomposition without a second engine
The port MUST model canonical upstream principles, skills, playbooks, roles and route behavior as distinct upstream-owned artifacts. The portable execution vocabulary MUST remain the existing 17 `agent.*`, `workspace.*`, `human.*`, `plan.update`, `schedule`, `monitor`, `session.*`, `evidence.capture` and `verify` capabilities until a separately accepted portability contract change proves another atomic postcondition is required. Swarm, Arena, Interrogate, Orchestrate, WorkPool, `model.role`, `agent.fan_out` and RPC message types MUST NOT be added as portable capability identifiers merely because a harness exposes their names. Recomposition MUST use canonical Markdown plus existing capability postconditions.

#### Scenario: port to a new harness that has WorkPool
- **GIVEN** a host exposes a native worker pool and pstack needs to run Arena
- **WHEN** a portability profile is authored
- **THEN** worker pool behavior is represented as a host dispatch mechanism satisfying `agent.spawn` and `agent.join`, with independence proven separately
- **AND** no portable WorkPool scheduler, engine, capability enum or duplicate playbook DSL is introduced

### Requirement: Capability postconditions drive behavioral parity
A host binding MUST record its native mechanism, `implementation_status`, `enforcement`, `verification_status` and source/version attribution using the existing `schemas/portability/binding.schema.json` and `capability.schema.json`. The route/playbook contract MUST state which observations make each required postcondition true. A source reference or syntactically valid binding alone MUST NOT establish observed live parity.

#### Scenario: mapped agent spawn lacks actual child terminal result
- **GIVEN** an OMP binding names `task` for `agent.spawn`
- **WHEN** its only evidence is a profile string comparison and a successful `omp --help` query
- **THEN** the binding MAY be static-only but MUST NOT be verified as an observed live spawn/join
- **AND** model-backed child identity, result and terminal outcome remain explicit acceptance gates

### Requirement: Intent router and native dispatch are separate boundaries
The pstack route resolver MUST remain the single portable source of route choice, step ordering and explicit skipped steps. The host adapter MUST translate only the selected playbook's required capabilities and files into native skill/agent invocations. Host discovery errors, aliases, namespace collisions and model role selectors MUST be handled at the adapter boundary and MUST NOT mutate the canonical route or role meaning.

#### Scenario: OMP namespaced skill collision
- **GIVEN** both user and installed package expose a `poteto-mode` skill
- **WHEN** OMP reports one bare skill and a namespaced alternative
- **THEN** the adapter resolves the expected skill origin and records the actual selection
- **AND** it does not silently reinterpret a different user's skill as canonical pstack

### Requirement: Execution briefs and workspace ownership are explicit
Each worker/verifier spawned by a compositional pstack playbook MUST receive a bounded standalone brief including goal, scope, immutable relevant revisions, verification method, deadline/budget, prohibited actions and report shape appropriate to the unit. Writable units MUST have non-overlapping ownership, an observed isolation mechanism or an explicit gap. A model instruction to avoid writes MUST be classified advisory unless the host actually enforces a read-only boundary.

#### Scenario: two Arena candidates write the same directory
- **GIVEN** two candidate agents require write access
- **WHEN** neither has an exclusive output path or isolated worktree
- **THEN** the adapter MUST reject that concurrency plan or serialize it without claiming parallel independent candidates
- **AND** passing static profile validation does not satisfy the workspace-isolation proof

### Requirement: Native host owns long-horizon durable state
A pstack adapter MUST use its host's existing session, task and approval facilities to implement the portable `session.*`, `agent.*`, `plan.update` and `monitor` postconditions when available. If the host cannot meet `schedule` or a durable nested-coordinator requirement, the adapter MUST declare `gap` or `adapted` rather than create a competing state store, scheduler, session manager or job database. A model-backed child-handle resume MUST NOT be inferred from a successful parent session resume.

#### Scenario: canonical orchestrate nests track coordinators
- **GIVEN** the pinned canonical Orchestrate playbook has coordinator, track sub-coordinator and worker ownership
- **WHEN** a port uses one flat parent with direct workers and host track state
- **THEN** the parity report classifies nested orchestration as adapted or gap until observed multi-level child ownership and joins exist
- **AND** the host's native durable state remains authoritative

### Requirement: Independent candidate and reviewer semantics survive composition
Swarm MUST fan out work under a frozen coverage or race rule and join completed child results before synthesis. Arena MUST freeze its scoring rubric before generation, isolate candidate artifacts, cross-judge only completed candidates, choose/graft a coherent base and run post-graft verification. Interrogate MUST use independent contexts and an identical review pack, preserve disagreement, produce lead dispositions and MUST NOT auto-apply fixes. A reused worker context MUST NOT be passed off as a fresh independent reviewer.

#### Scenario: WorkPool repeats reviewer context
- **GIVEN** OMP WorkPool reuses a warmed reviewer after the first Interrogate arm
- **WHEN** the host attempts to score a second arm as independent
- **THEN** the verifier rejects independence unless fresh-agent policy and distinct execution contexts are observed
- **AND** unavailable reviewers are recorded as gaps rather than consensus

#### Scenario: Swarm worker never returns
- **GIVEN** one required partition's worker times out
- **WHEN** the coordinator synthesizes completed worker output
- **THEN** the final report identifies the missing partition, worker disposition and any retry
- **AND** incomplete coverage cannot become a full PASS

### Requirement: Verification evidence shapes remain separate and existing
The port MUST reuse `binding.schema.json` for capability classification, `evidence.schema.json` for evidence ledger entries, and `receipt.schema.json` for the four-plane verification receipt without inventing new incompatible enums. The receipt scenario `evidence_level` MUST be `static | offline | observed_live | legacy`. The evidence-ledger `kind` field MUST retain its own `static | runtime | external` semantics; its verdict enum is narrower than the receipt verdict enum. A proposed cross-schema mapping MUST be explicit and schema-validated rather than silently collapsing unlike types. Source-documented/static/offline work MUST NOT prove an `observed_live` runtime claim. Revision freshness and evidence strength MUST be evaluated separately from nominal PASS/FAIL verdict.

#### Scenario: existing ledger and receipt distinguish untested execution
- **GIVEN** no OMP model-backed worker could run but offline profile checks passed
- **WHEN** evidence is serialized to the existing ledger and receipt schemas
- **THEN** each artifact validates independently, with any unsupported `UNTESTED` state recorded only in a schema that permits it
- **AND** the runtime plane cannot be promoted to verified or supported on the strength of static/offline evidence

### Requirement: Portable package projection preserves roles and lifecycle boundaries
A portable plugin descriptor MUST remain the single package-source authority. Each host projection MUST produce actual host-recognized skill and role artifacts required by the pinned playbooks, and prove discovery by host-native source attribution rather than file existence or generic `plugin list`. Package operations MUST preserve unmanaged user/project files and host settings; when plugin link/install operations target user-scoped roots, native tests MUST first prove the effective root is disposable.

#### Scenario: OMP install omits agents
- **GIVEN** OMP package projection includes skills and a generated pseudo-manifest but no installed `agents/*.md`
- **WHEN** an Arena cross-judge role is dispatched after install
- **THEN** package parity remains unverified until a native role agent actually resolves with the expected model role
- **AND** an installer smoke check cannot substitute for role execution evidence

### Requirement: Parity reports have independent canonical and runtime dimensions
A conformance report MUST distinguish: (1) coverage against the immutable `UPSTREAM` pin; (2) drift against newly observed upstream head; (3) per-host implementation/enforcement strength; (4) evidence level and current exact-revision native outcome; and (5) per-playbook semantic result `preserve | adapt | exclude | gap`. The test suite MUST include positive and negative fixtures for these dimensions. A missing host CLI or model provider MUST result in BLOCKED/UNTESTED where allowed, not invented PASS.

#### Scenario: green offline tests with unavailable native runner
- **GIVEN** all portable Python contract tests pass and an OMP model provider is unavailable
- **WHEN** the conformance gate evaluates the OMP adapter
- **THEN** pinned canonical coverage and offline conformance MAY pass while native OMP runtime remains BLOCKED/UNTESTED
- **AND** the overall label must not advertise complete cross-harness live behavioral parity

## Minimal data model

```yaml
Capability:
  id: string
  required_postconditions: [string]

Binding:
  host: string
  capability: string
  implementation_status: native | shim | version-gated | gap
  primitive: optional string
  enforcement: hard | soft | advisory
  verification_status: verified | static-only | unverified | stale

Adaptation:
  canonical_artifact: string
  mode: preserve | adapt | exclude | gap
  reason: optional string

Evidence:
  claim: string
  kind: static | runtime | external
  artifact: string
```

## Conformance floor

A harness seeking `supported` status MUST prove at least:

1. load/invoke pstack;
2. route one playbook;
3. update progress state;
4. spawn and join one worker;
5. fan out independent workers;
6. isolate a writer when required;
7. perform independent verification;
8. execute swarm;
9. execute arena;
10. execute interrogate;
11. run a real verification lever;
12. report unsupported optional capabilities explicitly.

Scheduling is required only when the adapter claims support for long-running playbooks that depend on it.
