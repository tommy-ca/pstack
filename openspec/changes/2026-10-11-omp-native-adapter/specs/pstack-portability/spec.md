# pstack-portability semantic building blocks — delta specification

This delta strengthens the existing `openspec/specs/pstack-portability/spec.md`; it does not replace its capability vocabulary or mandate a new workflow runtime. Full decomposition and data flow: `../../semantic-building-blocks.md`.

## ADDED Requirements

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

## MODIFIED Requirements

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
