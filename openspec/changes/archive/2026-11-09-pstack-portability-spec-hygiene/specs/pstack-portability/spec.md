# pstack-portability — Spec hygiene and 1,000-line ceiling reconciliation

## MODIFIED Requirements

### Requirement: Canonical intent is upstream-owned
Principles, skills, router behavior, playbook intent, roles, ordering, and verification rules MUST derive from the pinned official pstack tree. A host adapter MUST NOT become an intermediate source of truth for another host. A port MUST track two independent states: `pin_conformance` (covering the canonical pin) and `upstream_freshness` (unclassified newer canonical changes). A port MAY pass pin conformance while reporting upstream drift.

#### Scenario: reference port is not canonical

- **GIVEN** this repository
- **WHEN** portability behavior is reviewed
- **THEN** official pstack at `UPSTREAM` is the canonical authority
- **AND** this repository is reference evidence for host adaptation
- **AND** Codex, Claude Code, or future adapters do not normatively derive from the Grok mapping

### Requirement: Portable core stays small
The portable core MUST consist of canonical principles, skills, playbook intent, router semantics, roles, verification contracts, and declared host-bound semantic capabilities (agent lifecycle, workspace isolation, human gates, schedule/monitor, session persistence, and verification). The portability layer MUST NOT introduce a generic scheduler, task database, session manager, workflow DSL, provider gateway, or orchestration runtime when the host owns those concerns.

#### Scenario: new harness

- **GIVEN** a new agent harness
- **WHEN** pstack is ported to it
- **THEN** the porter maps the semantic capabilities to native primitives, shims, version-gated behavior, or explicit gaps
- **AND** canonical playbooks are not rewritten as a new workflow language

### Requirement: Harness tool mappings are structured and schema-validated
Each harness adapter profile MUST declare a typed `tool_mappings` object conforming to `schemas/tool-mapping.schema.json`. The mapping defines host primitives for file operations, command execution, network access, subagent lifecycle, background tasks, tool protocols, plan updates, and human questions. Upstream pstack skills MUST NOT hardcode host-specific execution commands; primitives are resolved dynamically from the active harness profile.

#### Scenario: tool mapping validation
- **GIVEN** a harness profile in `profiles/`
- **WHEN** portability verification executes
- **THEN** the profile's `tool_mappings` object validates against `schemas/tool-mapping.schema.json`
- **AND** missing or unmapped required capabilities fail the adapter gate

### Requirement: Swarm is a composition, not a harness primitive
The `swarm` skill MUST preserve this semantic shape: `frame -> fan-out -> join -> evidence validation -> aggregate -> report`. Workers MUST receive independent slices or explicitly declared race arms. Each brief MUST name goal, scope, verification method, and output contract. Missing or invalid worker evidence becomes a dropout or gap; a gap does not count as PASS. Required host capabilities are `agent.spawn` and `agent.join`.

#### Scenario: host cannot parallelize

- **GIVEN** a swarm whose independence is required
- **WHEN** the host cannot create independent child contexts
- **THEN** the adapter reports a gap
- **AND** sequential reasoning in one context is not labeled equivalent

### Requirement: Lever verification is the preferred proof pattern
The combination of **Build the Lever**, **Prove It Works**, and `create-verification-skill` defines the portable verification pattern. The port MUST prefer a deterministic lever over hand repetition. For non-trivial work, the adapter MUST prefer the smallest rerunnable script, codemod, generator, skill, or driver that proves the work with standard sections (Launch, Doctor, Drive, Proof Bar, Evidence, Cleanup). A deterministic lever SHOULD be preferred over subagent fan-out.

#### Scenario: completion claim

- **GIVEN** an implementation is declared done
- **WHEN** verification is available on the real artifact
- **THEN** the verifier drives that artifact and records evidence
- **AND** compilation, static checks, or child self-report alone do not substitute for runtime proof

### Requirement: Verification has three planes
The port MUST separate three conformance concerns: canonical pin/inventory/drift, adapter/native projection, and runtime observed behavior. In serialized receipts, these concerns MUST map to the four required verdict-bearing planes (`canonical`, `adapter`, `package`, `runtime`) in `schemas/receipt.schema.json`. The package plane audits manifest generation, install, and discovery. A positive result in one plane MUST NOT substitute for an absent mandatory result in another.

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
Portability changes MUST apply key design constraints: Laziness Protocol (smallest adapter that proves compatibility), Subtract Before You Add (delete dead abstractions before adding features), Build the Lever (codify checks in scripts), Boundary Discipline (keep host specifics in adapter profiles), and Prove It Works (require evidence receipts for claims). Adapters MUST NOT introduce speculative abstractions or wrapper layers that duplicate host capabilities.

#### Scenario: boundary enforcement

- **GIVEN** a new host adapter implementation
- **WHEN** host-specific configuration or syntax is processed
- **THEN** host primitives stop at the adapter boundary
- **AND** canonical playbooks remain host-neutral

### Requirement: Canonical semantic decomposition without a second engine
Playbook intent, review postures, and role definitions MUST resolve to canonical PStack behaviors rather than introducing an alternate execution engine. Adapters MAY adapt host-native dispatch conventions but MUST NOT alter canonical role contracts, prompt invariants, or verification criteria. Composite operations such as Swarm, Arena, and Interrogate MUST compose existing portable primitives rather than requiring bespoke runtime primitives.

#### Scenario: port to a new harness that has WorkPool
- **GIVEN** a host exposes a native worker pool and pstack needs to run Arena
- **WHEN** a portability profile is authored
- **THEN** worker pool behavior is represented as a host dispatch mechanism satisfying `agent.spawn` and `agent.join`, with independence proven separately
- **AND** no portable WorkPool scheduler, engine, capability enum or duplicate playbook DSL is introduced

### Requirement: Native host owns long-horizon durable state
A pstack adapter MUST use host session, task, and approval facilities to implement `session.*`, `agent.*`, `plan.update`, and `monitor` postconditions when available. If the host cannot meet `schedule` or durable nested coordination, the adapter MUST declare `gap` or `adapted` rather than create a competing state store, scheduler, session manager, or job database. Child-handle resume MUST NOT be inferred from parent session resume.

#### Scenario: canonical orchestrate nests track coordinators
- **GIVEN** the pinned canonical Orchestrate playbook has coordinator, track sub-coordinator and worker ownership
- **WHEN** a port uses one flat parent with direct workers and host track state
- **THEN** the parity report classifies nested orchestration as adapted or gap until observed multi-level child ownership and joins exist
- **AND** the host's native durable state remains authoritative

### Requirement: Independent candidate and reviewer semantics survive composition
Swarm MUST fan out work under a frozen coverage or race rule and join completed child results before synthesis. Arena MUST freeze its scoring rubric before generation, isolate candidate artifacts, cross-judge only completed candidates, choose/graft a base, and verify post-graft. Interrogate MUST use independent contexts with identical review packs, preserve disagreement, and produce lead dispositions without auto-applying fixes. Context reuse is prohibited for reviewers.

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
The port MUST reuse `binding.schema.json` for classification, `evidence.schema.json` for ledger entries, and `receipt.schema.json` for four-plane receipts. Receipt evidence levels MUST be `static | offline | observed_live | legacy`. The evidence ledger `kind` MUST retain `static | runtime | external`. Static work MUST NOT prove `observed_live` runtime claims. For candidate Pi, preflights without tools MUST NOT cause runtime PASS; verifier remains BLOCKED until native receipts exist.

#### Scenario: existing ledger and receipt distinguish untested execution
- **GIVEN** no OMP model-backed worker could run but offline profile checks passed
- **WHEN** evidence is serialized to the existing ledger and receipt schemas
- **THEN** each artifact validates independently, with any unsupported `UNTESTED` state recorded only in a schema that permits it
- **AND** the runtime plane cannot be promoted to verified or supported on the strength of static/offline evidence

#### Scenario: Pi preflight succeeds but child never launches
- **GIVEN** a Pi executable, matching package versions and `--no-tools` echo return 0
- **WHEN** `scripts/prove_pi_vertical_slice.py` reduces its four-plane receipt
- **THEN** the runtime plane and overall verdict MUST remain BLOCKED
- **AND** there MUST NOT be an `observed_live` child/sandbox scenario until actual child authorization and effects are recorded

#### Scenario: cleanup has no actual actor tracking
- **GIVEN** the Pi preflight has no known child ID, worktree or sandbox-effect ledger
- **WHEN** its cleanup wrapper runs
- **THEN** it MUST return BLOCKED/NOT_VERIFIED rather than PASS
- **AND** a lack of detected side effects MUST NOT be described as proof of cleanup

### Requirement: Portable package projection preserves roles and lifecycle boundaries
A portable plugin descriptor MUST remain the single package-source authority. Each host projection MUST produce host-recognized skill and role artifacts required by pinned playbooks, proving discovery by native source attribution. Package operations MUST preserve unmanaged user files and host settings. For candidate Pi, package projection is a thin opt-in skills resource projection without bundled executable extensions; package absence remains PACKAGE GAP.

#### Scenario: OMP install omits agents
- **GIVEN** OMP package projection includes skills and a generated pseudo-manifest but no installed `agents/*.md`
- **WHEN** an Arena cross-judge role is dispatched after install
- **THEN** package parity remains unverified until a native role agent actually resolves with the expected model role
- **AND** an installer smoke check cannot substitute for role execution evidence

#### Scenario: Pi skills installed without role definitions
- **GIVEN** Pi loads PStack's `poteto-mode` skill through an opt-in `pi.skills` package
- **WHEN** a PStack named subagent role is requested in a separate consumer project
- **THEN** the package plane MUST remain GAP/BLOCKED unless `pi-subagents` actually resolves the corresponding `agents/*.md` definition
- **AND** `pi.skills` presence alone MUST NOT claim role or runtime parity

#### Scenario: Unreviewed extension package auto-install
- **GIVEN** a PStack Pi package would auto-include third-party Pi extension code or a transitional competing PStack package
- **WHEN** a packaging review runs
- **THEN** it MUST reject the bundled extension or require an explicit, separately reviewed user opt-in
- **AND** no untrusted package activation may be claimed as PStack security enforcement

### Requirement: Parity reports have independent canonical and runtime dimensions
A conformance report MUST distinguish: (1) coverage against the immutable `UPSTREAM` pin; (2) drift against newly observed upstream head; (3) per-host implementation strength; (4) evidence level and exact-revision native outcome; and (5) per-playbook semantic result (`preserve | adapt | exclude | gap`). The test suite MUST include positive and negative fixtures. A missing host CLI or provider MUST result in BLOCKED/UNTESTED where allowed, never an invented PASS.

#### Scenario: green offline tests with unavailable native runner
- **GIVEN** all portable Python contract tests pass and an OMP model provider is unavailable
- **WHEN** the conformance gate evaluates the OMP adapter
- **THEN** pinned canonical coverage and offline conformance MAY pass while native OMP runtime remains BLOCKED/UNTESTED
- **AND** the overall label must not advertise complete cross-harness live behavioral parity
