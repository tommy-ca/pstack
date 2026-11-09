# pstack-portability Specification

## Purpose

Define the smallest portable contract that preserves canonical pstack intent across agent harnesses without introducing a second workflow runtime.

Official `cursor/plugins/pstack` at the immutable `UPSTREAM` pin is the canonical source. This repository is a reference port. Grok Build is the strongest reference adapter in this tree; Codex and Claude Code have mapping/packaging surfaces whose runtime support must be proven separately.

## Requirements

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
Each harness adapter profile MUST declare a typed `tool_mappings` object conforming to `schemas/tool-mapping.schema.json`. The mapping defines host primitives for file operations, command execution, network access, subagent lifecycle, background tasks, tool protocols, plan updates, and human questions. Upstream pstack skills MUST NOT hardcode host-specific execution commands; primitives are resolved dynamically from the active harness profile.

#### Scenario: tool mapping validation
- **GIVEN** a harness profile in `profiles/`
- **WHEN** portability verification executes
- **THEN** the profile's `tool_mappings` object validates against `schemas/tool-mapping.schema.json`
- **AND** missing or unmapped required capabilities fail the adapter gate

### Requirement: Harness runtime conventions are structured and schema-validated

Each harness adapter profile MUST declare a typed `runtime_conventions` object conforming to `schemas/runtime-conventions.schema.json`.

The runtime conventions define maximum subagent depth (`max_subagent_depth`), supported workspace isolation modes (`supported_isolation_modes`), default model slug (`default_model`), allowed model-facing spawn fields (`allowed_spawn_fields`), forbidden spawn fields (`forbidden_spawn_fields`), and optional wire aliases (`wire_aliases`).

#### Scenario: runtime convention validation
- **GIVEN** a harness profile in `profiles/`
- **WHEN** portability verification executes
- **THEN** `runtime_conventions` validates against `schemas/runtime-conventions.schema.json`
- **AND** subagent recursion depth exceeding the configured maximum is rejected

### Requirement: Skill order resolution follows a declared 3-tier fallback matrix

Each harness adapter profile MUST declare an ordered `skill_order` list conforming to `schemas/skill-order.schema.json`.

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
The `swarm` skill MUST preserve this semantic shape: `frame -> fan-out -> join -> evidence validation -> aggregate -> report`. Workers MUST receive independent slices or explicitly declared race arms. Each brief MUST name goal, scope, verification method, and output contract. Missing or invalid worker evidence becomes a dropout or gap; a gap does not count as PASS. Required host capabilities are `agent.spawn` and `agent.join`.

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
The combination of **Build the Lever**, **Prove It Works**, and `create-verification-skill` defines the portable verification pattern. The port MUST prefer a deterministic lever over hand repetition. For non-trivial work, the adapter MUST prefer the smallest rerunnable script, codemod, generator, skill, or driver that proves the work with standard sections (Launch, Doctor, Drive, Proof Bar, Evidence, Cleanup). A deterministic lever SHOULD be preferred over subagent fan-out.

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
Playbook intent, review postures, and role definitions MUST resolve to canonical PStack behaviors rather than introducing an alternate execution engine. Adapters MAY adapt host-native dispatch conventions but MUST NOT alter canonical role contracts, prompt invariants, or verification criteria. Composite operations such as Swarm, Arena, and Interrogate MUST compose existing portable primitives rather than requiring bespoke runtime primitives.

#### Scenario: port to a new harness that has WorkPool
- **GIVEN** a host exposes a native worker pool and pstack needs to run Arena
- **WHEN** a portability profile is authored
- **THEN** worker pool behavior is represented as a host dispatch mechanism satisfying `agent.spawn` and `agent.join`, with independence proven separately
- **AND** no portable WorkPool scheduler, engine, capability enum or duplicate playbook DSL is introduced

### Requirement: Capability postconditions drive behavioral parity
A host binding MUST record its native mechanism, `implementation_status`, `enforcement`, `verification_status` and source/version attribution using the existing `schemas/binding.schema.json` and `capability.schema.json`. The route/playbook contract MUST state which observations make each required postcondition true. A source reference or syntactically valid binding alone MUST NOT establish observed live parity.

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

### Requirement: Model catalog discovery and proof are host-specific

Native model availability, allowed effort tokens and spawn fields MUST be resolved from the actual host version. Checked-in models and reference-port tests MUST NOT authorize a live dispatch claim. Capability-specific evidence from one host MUST NOT upgrade another host's `verified` status.

#### Scenario: unsupported model or effort

- **GIVEN** a model slug or effort token absent from the live host catalog
- **WHEN** role resolution validates an explicit request
- **THEN** it stops with an actionable unsupported-choice error
- **AND** it does not silently substitute a different named model

#### Scenario: a Pi reference proves a feature but OMP does not

- **GIVEN** a tested mechanism in the Pi extension of pstack-claude
- **WHEN** the target OMP profile is audited
- **THEN** that mechanism is only a candidate pattern
- **AND** OMP requires its own native evidence receipt to advance status

### Requirement: Logical model/role policy is typed and harness-neutral

A policy document MUST conform to `schemas/portability/model-role-policy.schema.json`. `pstack.package.json#/roles` MUST remain the only canonical role registry; the policy MAY add per-role constraints but MUST NOT duplicate role definitions or tier names. It MUST reuse the six `default_model_role` tier values. Host records MUST separate catalogs from role policy. Unknown roles, tiers, or dangling references MUST fail validation.

#### Scenario: new harness

- **GIVEN** an additional host with native model identifiers
- **WHEN** a portable canonical role is resolved
- **THEN** it uses that host's validated catalog and declared tier mapping
- **AND** the shared skill/playbook remains unchanged

### Requirement: Model and effort selection is deterministic and conservative

Policy/safety/approval constraints are enforced before choosing a model. Within eligible choices, precedence is explicit invocation, project override, user override, host role override, host tier default, and parent inheritance. `inherit-parent`/`auto` MUST omit model from native spawn arguments. A role MUST NOT dispatch an unavailable real slug or an unsupported effort token. Runtime-discovered model/effort data MUST carry host version and freshness evidence.

#### Scenario: explicit unavailable model

- **GIVEN** an explicit model not offered by the host
- **WHEN** resolution executes
- **THEN** it reports a gap requiring a user decision
- **AND** it does not silently fall back to a different named model

#### Scenario: inherited model

- **GIVEN** a role configured as `inherit-parent`
- **WHEN** its host-native spawn is built
- **THEN** the model field is omitted
- **AND** model inheritance is described as host behavior, not invented model identity

### Requirement: Panels and cross-judges preserve independence

Panel slots MUST be discrete agent invocations. An Arena cross-judge seat MUST differ from the candidate family when required and available; an Interrogate reviewer panel MUST preserve its declared independent-model family diversity; otherwise the verifier MUST report a degraded or blocked independence condition, rather than claiming multi-model review. Required agent.spawn/agent.join and workspace isolation bindings MUST be checked before fan-out.

#### Scenario: only one live model family

- **GIVEN** a cross-judge policy requires family diversity but host discovery identifies only one family
- **WHEN** the panel is planned
- **THEN** the diversity claim cannot pass
- **AND** a degraded/fallback plan or explicit block is recorded

### Requirement: Hook routing has a host-scoped, reversible lifecycle

Host-native routing hooks MAY inject canonical poteto-mode intent only when the package and host permit it. Setup MUST support opt-out and validate startup/resume/compact semantics where available. Hook deployment MUST be idempotent and MUST NOT introduce a parallel orchestration state store.

#### Scenario: routing disabled

- **GIVEN** the user's host-specific setup disables the session hook
- **WHEN** a new session starts or resumes
- **THEN** pstack does not inject an automatic routing instruction
- **AND** explicitly invoked skills still work

### Requirement: Cross-port imports are provenance-filtered

Transfer from `michael-denyer/pstack-claude` MUST identify source commit, license/NOTICE implications, canonical-equivalent behavior, adapter-only behavior, and declared `tools/forks.json` policy modifications. Pstack MUST preserve host-owned durable orchestration state and qstack's post-router domain overlay.

#### Scenario: reference has a policy fork

- **GIVEN** a reference change intentionally differs from canonical upstream
- **WHEN** the porting graph classifies it
- **THEN** the policy change is reviewed separately and not silently imported
- **AND** no pstack or qstack router/state fork is created by default

### Requirement: Claims advance by independently verified gates

Every host addition progresses through candidate, mapped, packaged, verified and supported only with evidence appropriate to that state. Static tests, generated manifests and mock simulations alone MUST NOT promote runtime-supported claims. Swarm/Arena/Interrogate multi-model results MUST cite independently executed runs or remain explicitly pending.

#### Scenario: package projects successfully but live runtime fails

- **GIVEN** projected manifests and JSON schemas pass
- **WHEN** the native host fails to dispatch a configured role
- **THEN** runtime status remains unverified or failed
- **AND** the evidence ledger records the failure without overwriting previous receipts

### Requirement: Role/model resolution is a pure, auditable plan before native dispatch

A role resolver MUST produce a deterministic `ModelPlan` without spawning children or asserting model availability. The planner MUST report `PLANNED`, `DEGRADED` or `BLOCKED` as planning states, never runtime verdicts. Source precedence MUST be explicit → project → user → host role → host tier → inherited parent or fail-closed. Host metadata MUST NOT count as verified runtime receipts.

#### Scenario: explicit configuration overrides project and user choices

- **GIVEN** a canonical role, eligible host catalog, and different explicit, project and user model selections
- **WHEN** the pure resolver runs
- **THEN** explicit wins and the selected origin is recorded in the plan
- **AND** the plan is labeled `static-planning-only`
- **AND** the host must separately prove real invocation

#### Scenario: unsupported explicit model fails rather than downgrading

- **GIVEN** a requested explicit model missing from the declared host catalog
- **WHEN** role planning runs
- **THEN** the plan is `BLOCKED` with a named-missing-model reason
- **AND** no parent-inheritance or guessed substitute is dispatched

### Requirement: Independent seats and model diversity are distinct measures

Role settings MAY declare a bounded `seats` count independent of configured model slugs. A panel MAY use one model for multiple fresh-context seats but MUST record reduced family diversity. The canonical one-runner default MUST remain possible. The Arena cross-judge pool MUST select one eligible seat preferring a different family. Interrogate reviewers MUST count independent sessions and families separately.

#### Scenario: three Arena candidates using one configured model

- **GIVEN** one configured model and `seats=3`
- **WHEN** Arena plans its candidate fan-out
- **THEN** three independent planned seats are produced with unique ordinal identifiers
- **AND** the report states only one configured model and model family
- **AND** true session independence remains pending host-native evidence

#### Scenario: single canonical-default Arena runner

- **GIVEN** no user-requested multi-candidate configuration
- **WHEN** the canonical default resolves to one runner
- **THEN** role planning permits one candidate
- **AND** no implicit two-runner requirement is inserted by this port

### Requirement: Planner output is typed and cannot masquerade as runtime proof

`ModelPlan` MUST conform to `schemas/portability/model-plan.schema.json`. The output schema MUST reject runtime verdict statuses and evidence-level upgrades, carry immutable seat ordinals, and distinguish an inherited model's unknown provider/family from detected real model identity.

#### Scenario: static plan cannot become a fake verified receipt

- **GIVEN** a structurally valid static `ModelPlan`
- **WHEN** its status is changed to `VERIFIED` or evidence level to `runtime-verified`
- **THEN** JSON Schema validation fails
- **AND** host-native runtime proof remains a separate capability receipt

#### Scenario: blocked planning result

- **GIVEN** a model not present in the host's declared catalog
- **WHEN** the pure role planner returns `BLOCKED`
- **THEN** the output has no planned seats and at least one explicit reason
- **AND** the plan validates as an honest error artifact

### Requirement: Harness identity can extend without replicating the workflow router

The design MUST support future harness identities through a versioned declarative adapter descriptor, not one undifferentiated `custom` entry. Until a migration is tested, known-host enums stay operational and new IDs are NOT runtime-supported. A new identity MUST NOT inherit verified capabilities, tool mappings, or model availability. Shared skill and playbook content MUST remain unchanged.

#### Scenario: two new candidate harnesses

- **GIVEN** two distinct future harness descriptors that are not in the current six-host inventory
- **WHEN** they are validated as candidate adapters by a future extensible registry
- **THEN** their identities and model catalogs cannot collide or alias to `custom` as the same host
- **AND** no native capability becomes `verified` or `supported` merely by registry insertion
- **AND** the current six hosts continue to validate and project without drift

#### Scenario: attempted untrusted host alias

- **GIVEN** a proposed adapter identity colliding with a built-in host or containing path traversal
- **WHEN** the registry resolves its manifest
- **THEN** the descriptor is rejected without executing any provider code
- **AND** no host tool mapping or user config file is rewritten

### Requirement: Three-way port comparisons distinguish normative and reference evidence

Every reference-port proposed change MUST bind canonical commit, comparator commit, prior comparator commit, target revision and relevant artifact path. A reference implementation MUST NOT be used as canonical authority. Classification MUST include `preserve`, `adapt`, `exclude`, `policy-fork` or `gap`, postcondition, owner plane and evidence strength. Canonical freshness and comparator freshness MUST be tracked independently.

#### Scenario: Reference gains a Pi capability

- **GIVEN** reference `pstack-claude` adds a passing Pi test after the pinned baseline
- **WHEN** target OMP or another harness is compared
- **THEN** the test is a candidate host-specific conformance scenario
- **AND** no target harness status changes without same-host observed evidence

#### Scenario: Canonical HEAD newer than applied pin

- **GIVEN** canonical main at 0.15.29 and applied port pin at 0.15.21
- **WHEN** a shared skill is classified from current canonical
- **THEN** the changed behavior is recorded as an unapplied upstream delta
- **AND** the applied upstream pin MUST remain unchanged until the #629/#630 gates are satisfied

### Requirement: Agent activity is observational and cannot corrupt settlement truth

A host adapter that exposes running agent activity MUST correlate concurrent tool calls by stable call identity and MUST clear activity after the owning agent has ended. Activity summaries MUST NOT be written as durable session messages or used as a substitute for successful child completion. Other hosts lacking an equivalent surface MUST report a capability GAP rather than simulate native observability.

#### Scenario: Two concurrent tool calls

- **GIVEN** a child has concurrent calls A and B
- **WHEN** A completes while B continues
- **THEN** B remains marked running until B's own settlement
- **AND** no fabricated overall child completion receipt is produced

#### Scenario: Agent stopped or resumed

- **GIVEN** an agent has stopped or a saved session is reloaded
- **WHEN** current activity is listed
- **THEN** ended agents have no live activity
- **AND** stale persisted fields cannot be presented as new execution

### Requirement: Child teardown and worktree cleanup fail safe

A host MAY terminate only the child process/session it still owns and MUST NOT infer success before actual native settlement. Worktree cleanup MUST retain output when untracked, ignored, locked, committed or submodule changes may exist, even when user/worktree Git configuration hides them from ordinary status output. Cleanup MUST NOT mutate a user's Git configuration to obtain evidence.

#### Scenario: Hidden untracked output

- **GIVEN** `status.showUntrackedFiles=no` hides an output file
- **WHEN** worktree cleanup evaluates safety
- **THEN** the worktree and branch are retained
- **AND** evidence cites the hidden output rather than calling the checkout clean

#### Scenario: Concurrent cancellation

- **GIVEN** a child has finished and its process identity may have changed
- **WHEN** a retrying cancellation request arrives
- **THEN** the operation is idempotent and does not kill any unrelated process
- **AND** a native stop receipt is emitted only for observed settlement

### Requirement: Model and reviewer diversity claims are host-evidence-backed

A role/model alias in a reference generator MUST NOT imply model availability in another host. Fanout counts MUST distinguish requested, dispatched, settled and independently verified seats; diversity MUST be supported by observed model/provider-family identity when required by the selected review topology. Degraded and blocked verdicts remain explicit.

#### Scenario: One model called twice

- **GIVEN** two fresh independent invocations use the same model family
- **WHEN** a workflow requiring multi-family Interrogate is evaluated
- **THEN** it MAY record two independently invoked seats
- **BUT** it MUST NOT claim cross-family model diversity

### Requirement: Recursive execution reuses existing gates

A new comparator audit MAY generate bounded follow-up tasks but MUST reuse existing canonical-sync, shipping and native-host promotion gates when they cover the same postcondition. Closed prior programs MUST NOT be reopened merely because a reference source advanced. Every new issue MUST name upstream/source revision, owner boundary, dependency, acceptance test and existing related issue.

#### Scenario: Comparator lifecycle defect intersects upstream sync

- **GIVEN** a comparator case reveals a shared lifecycle invariant already owned by #626
- **WHEN** the new delta is classified
- **THEN** link the concrete negative case to #626 and its existing verifier
- **AND** do not create a second runtime or redundant final acceptance gate

### Requirement: Standalone Pi is not OMP

A standalone Pi port MUST use its own declared candidate identity and native tool mapping. It MUST NOT reuse OMP process, session, RPC or evidence paths as observed Pi proof. Candidate identity MUST NOT be inserted into the six built-in host targets before native packaging and proof pass.

#### Scenario: Candidate profile without native proof
- **GIVEN** Pi core and extension documentation but no installed Pi runtime
- **WHEN** the adapter map is reviewed
- **THEN** each mapping has static-only or unverified status
- **AND** no Pi receipt is promoted to observed live
- **AND** the existing six shipped hosts remain unchanged

### Requirement: Minimal Pi extension ownership

Native Pi MUST own its MCP, codemode, tool-search, sessions and model/tool lifecycles. Exactly one delegated-agent engine SHOULD be active for PStack execution. Other extensions MUST be justified by a required capability or measured workload. Workflow policy MUST stay with canonical PStack semantics.

#### Scenario: Competing delegate engines
- **GIVEN** both pi-subagents and pi-dynamic-workflows are enabled
- **WHEN** the Pi/PStack profile is composed
- **THEN** the default profile MUST refuse ambiguous delegation ownership or disable the nonselected engine
- **AND** must not create two task ledgers

### Requirement: Pi interactive human decisions do not bypass authorization

The interactive candidate profile SHOULD provide `pi-ask-user` to implement structured `human.ask`. A successful `ask_user` response MUST NOT alone prove `human.gate` or hard permission enforcement. Every effect requiring approval MUST have an independently mediated authorization decision, including child launches and noninteractive/headless modes.

#### Scenario: Noninteractive agent requests unsafe operation
- **GIVEN** a headless Pi run without a permitted human gate
- **WHEN** an agent requests an effect that requires operator consent
- **THEN** execution MUST remain blocked pending separately authenticated authorization
- **AND** an `ask_user` fallback or pre-filled prompt MUST NOT authorize the effect

### Requirement: Pi autonomous approval and structured selection have separate owners

The Pi candidate SHOULD use `pi-verdict` for ordinary pre-tool-call risk adjudication and `pi-ask-user` for structured operator selections. These do not replace PStack's independently enforced `human.gate`, and a classifier `allow` MUST NOT override hard-deny policy. A missing or disabled permission extension MUST NOT silently authorize privileged actions. PStack MUST NOT infer full audit coverage from the plugin's gray-zone-only record.

#### Scenario: Classifier allows a privileged action
- **GIVEN** a PStack risk policy requiring independent human authorization
- **WHEN** pi-verdict returns `allow` or a fallback classifier rescues a failed first layer
- **THEN** the host MUST block the effect until independently authorized
- **AND** no hard-gate receipt may derive solely from the classifier opinion

#### Scenario: Missing gate or headless uncertain decision
- **GIVEN** an unsafe tool effect with a disabled, absent or uncertain gate
- **WHEN** the native actor executes without an operator
- **THEN** a separate mandatory permission boundary MUST deny the action
- **AND** an `ask_user` fallback MUST NOT bypass that denial

#### Scenario: Child launch and nested tool call
- **GIVEN** a `pi-subagents` delegated child or MCP/codemode nested call
- **WHEN** that action crosses a permission boundary
- **THEN** native tests MUST observe authorization for that actor and effect
- **AND** untested inherited extension behavior MUST remain UNTESTED, not PASS

### Requirement: Delegation extension owns schedules and lifecycle receipts

If installed `pi-subagents` exposes `mission.*`, `schedule.*`, and `subagent_launch`, the adapter MAY bind PStack `schedule` and `monitor` through version-gated primitives, but MUST NOT add a PStack-owned scheduler/mission database. Native proof MUST test permission-denied child launch, legacy background resume refusal, schedule restoration and terminal status without falsely promoting source documentation.

#### Scenario: Permission extension denies workflow child
- **GIVEN** a policy that denies the `subagent_launch` tool action
- **WHEN** a Pi workflow attempts to create that child
- **THEN** the child MUST NOT run and the parent MUST report a blocked outcome
- **AND** no acceptance receipt may record PASS

### Requirement: Sandbox claims are evidence-bound

A sandbox extension's installed state MUST NOT imply enabled task confinement. Parent, child and background actor profiles MUST be measured independently where applicable. A permission tool-hook or trusted extension exception MUST NOT be reported as an OS boundary.

#### Scenario: Credentials and outside-project defaults
- **GIVEN** a newly configured subagent policy with broad file/credential defaults
- **WHEN** a privileged child attempts to read or alter stored credentials or outside-project files
- **THEN** the verifier MUST explicitly check and record the effective policy
- **AND** PStack MUST NOT claim read-only or least-privilege enforcement from the installed sandbox alone

#### Scenario: Child trusted-tool bypass
- **GIVEN** a read-only confined child and a trusted extension tool that can mutate files
- **WHEN** the child attempts the mutation
- **THEN** the verifier MUST record actual admission and filesystem effects
- **AND** any mutation outside policy MUST FAIL the isolation claim
- **AND** a refusal or untested tool MUST NOT be promoted to PASS

### Requirement: Functional and formal verification reuse existing levers

The Pi candidate MUST reuse the existing three-tier verification skill machinery, receipt evidence, and create/maintain formal-verification procedures. No new generic proof registry may be introduced. Formal model checking MUST identify code correspondence, bounds, version, sync commit and at least one failing mutant.

#### Scenario: Model passes but code diverged
- **GIVEN** a formal model verified against a prior revision
- **WHEN** covered implementation code changes
- **THEN** the result MUST remain stale/unverified until reviewed and rerun
- **AND** completion MUST NOT be claimed from the old model PASS

### Requirement: LLMWiki records candidate status truthfully

The Pi semantic crosswalk MUST be curated in the existing self-contained .llm-wiki and keep raw source ingestion separate from authored knowledge. Sources MAY be cited externally in a candidate page but MUST NOT be represented as locally ingested immutable sources without a digest-bearing ingest record.

#### Scenario: External citation without local ingest
- **GIVEN** a candidate Pi mapping with public documentation links
- **WHEN** the LLMWiki is checked
- **THEN** the article identifies the citation as external/provisional
- **AND** no raw source digest or runtime conformance is invented

### Requirement: Each semantic adoption is attributable to three frozen revisions

Every proposed comparator adoption MUST identify normative Cursor source path and SHA, comparator path and SHA, target path or explicit missing owner, classification, postcondition, evidence tier and negative control. Comparator tools/forks.json policy deviations MUST NOT automatically override canonical upstream.

#### Scenario: Comparator fork changes review behavior
- **GIVEN** the comparator declares a skill path as a policy fork
- **WHEN** an audit proposes an identical target skill change
- **THEN** the audit MUST classify the fork and name which Cursor canonical invariant it preserves or intentionally changes
- **AND** the change MUST NOT be called an upstream sync without evidence from Cursor PStack

#### Scenario: GitHub compare truncates its file list
- **GIVEN** the compare response reports 86 commits but exposes a 300-file cap
- **WHEN** the audit claims coverage
- **THEN** it MUST record the cap and list audited paths explicitly
- **AND** it MUST NOT claim exhaustive file coverage until a complete scoped manifest is obtained

### Requirement: Cross-port capability equivalence is behavioral, host-scoped and graded

A reference-port tool alias, model alias, status matrix or documented live test MUST NOT promote any target host CapabilityBinding. Each host's own driver MUST prove the operation and its terminal side effects. The six declared host_targets MUST remain unchanged by importing comparator coverage.

#### Scenario: Reference Pi RPC reports background agent completion
- **GIVEN** a comparator test verifies completed child exit with an agentId
- **WHEN** target PStack maps agent.join or monitor for another host
- **THEN** the target MUST reproduce its own native child-ID, exit, transcript and terminal-state postconditions
- **AND** source-only evidence MUST remain static-only or unverified

#### Scenario: User choice versus hard authorization
- **GIVEN** a headless or nested child has no interactive ask-user UI
- **WHEN** a tool asks for a human gate
- **THEN** absent a verified enforcement mechanism the operation MUST fail closed
- **AND** human.ask support MUST NOT be substituted for human.gate

### Requirement: Termination, worktree and scheduler negative controls fail when broken

An adopted runtime invariant MUST have a safe, bounded negative mutation or fault injection that is observed to fail before it is accepted. A positive path without the inverse control is not complete verification.

#### Scenario: Cancelled child reports a stale completed transcript
- **GIVEN** the driver owns a child and has recorded the exact child ID
- **WHEN** cancellation settles before the child successfully joins
- **THEN** the receipt MUST identify a cancelled terminal state, never PASS
- **AND** the driver MUST NOT report another run's output under that child ID

#### Scenario: Git ignores a child-created file
- **GIVEN** an owned worktree contains new ignored or untracked output or an unmerged child commit
- **WHEN** the cleanup routine decides whether to delete
- **THEN** it MUST retain data and identify the obstruction
- **AND** it MUST NOT trust a Git status configuration that omits those files

#### Scenario: Timer is cancelled before callback delivery
- **GIVEN** a host-local schedule has a pending callback
- **WHEN** stop/cancel runs and the callback becomes due
- **THEN** no late schedule request may rearm or deliver a forbidden prompt
- **AND** the result MUST be verified against actual host semantics or marked unverified

### Requirement: Formal properties map to concrete target code with disclosed bounds

The create-formal-verification-skill workflow MUST bind model transitions to exact target implementation boundaries and preserve checker version, assumptions, fairness constraints and finite bounds. A foreign-port TLA+/Lean result is only a research reference, not a target proof.

#### Scenario: Reference wakeup model assumes an idle interval
- **GIVEN** the comparator's PiScheduler model requires host idle/timer fairness for eventual delivery
- **WHEN** the same liveness property is proposed for a target host
- **THEN** the target model MUST identify a code-level hook/dispatch mapping and prove or explicitly assume the idle condition
- **AND** a counterexample without the assumption MUST be reviewed, not hidden by strengthening fairness silently

#### Scenario: No model checker is available
- **GIVEN** a formal property and mutation model have been drafted
- **WHEN** TLC, Lean, or the selected verifier is unavailable
- **THEN** the formal result is BLOCKED, not PASS
- **AND** the generated verification skill states how to install/rerun the specific checker and the uncovered scope

### Requirement: Knowledge and reviewer receipts preserve their own authority boundaries

A wiki analysis MAY describe a source-only architectural candidate but MUST NOT assert locally ingested source immutability without write-once ingestion and source hash verification. Swarm, Arena and Interrogate MUST distinguish intended reviewer topology from executed seats and exact model families.

#### Scenario: Add a comparator semantic analysis to the wiki
- **GIVEN** an analytical page links only externally pinned source paths
- **WHEN** it is included in the generated wiki index
- **THEN** it MUST say source review only and list unverified runtime assertions
- **AND** source ingestion / hash proof MUST NOT be claimed until scripts/llm_wiki.py ingest and verify-sources pass

#### Scenario: Simulated multi-model reviewer panel
- **GIVEN** only one reviewer model or no real child invocation exists
- **WHEN** a PR runs the Swarm/Arena/Interrogate checklist
- **THEN** it MAY record proposed lanes and single-model findings
- **BUT** it MUST NOT report independent multi-model agreement or an exact-head independent acceptance verdict

### Requirement: Release retains the existing acceptance and rollback boundaries

A source-only documentation or skill-update PR MUST NOT change pstack.package.json, UPSTREAM, profiles, active process orchestration or a previously completed issue's verification claims without their distinct promotion gates.

#### Scenario: Source-level audit succeeds but native runtime verification is unavailable
- **GIVEN** the OpenSpec, wiki and skill instructions are updated
- **WHEN** no real target host execution or independent model verdict exists
- **THEN** the documentation slice MAY be reviewed independently
- **AND** all native/formal/reviewer gates MUST remain open, BLOCKED or UNTESTED as applicable

### Requirement: Three-source cross-port comparisons bind canonical and comparator pins

Every three-source semantic audit MUST record exact commit SHAs and licensing provenance for canonical Cursor PStack, reference comparator `pstack-claude`, and target `tommy-ca/pstack`. Declared comparator policy forks (`tools/forks.json`) MUST be explicitly classified into `adapt`, `preserve`, `exclude`, or `policy-fork`. No policy fork MAY be promoted to canonical without formal acceptance.

#### Scenario: Comparator policy fork is triaged
- **GIVEN** a declared fork in comparator `tools/forks.json`
- **WHEN** evaluated against canonical intent and target host requirements
- **THEN** it is classified in `docs/research/pstack-claude-forks-2026-11-06.json`
- **AND** comparator-specific policy modifications are not applied as canonical behavior

### Requirement: Failure-oriented negative postconditions are verifiable across hosts

Contract verifiers MUST enforce negative failure postconditions:
1. Canceled or terminated children must fail closed and never report PASS.
2. Tool completion must correlate with exact invocation ID.
3. Worktree cleanup must fail safe when untracked or uncommitted files exist.
4. Authorization requests without explicit grant must deny.
5. Canceled timers must not deliver late wakeups.

#### Scenario: Headless permission request without explicit grant
- **GIVEN** a headless execution context requiring human permission
- **WHEN** no interactive terminal or pre-authorized rule exists
- **THEN** the request denies fail-closed
- **AND** no execution proceeds

### Requirement: Pi extension ownership and source-pinned upgrades stay explicit
Standalone Pi MUST remain a separate candidate host from OMP with explicit delegation, OS sandbox, tool adjudication, and human.ask capabilities. Pinned packages are pi-subagents 0.86.0, pi-better-sandbox 0.14.1, pi-verdict 0.16.0, and pi-ask-user 0.17.2, with pi-web-access 0.47.0 as optional research. Newer releases such as 0.87.0 require independent verification before changing the active pin.

#### Scenario: provider-qualified model would fall back
- **GIVEN** a future upgrade probe names `provider/id` and the chosen provider is not authorized
- **WHEN** Pi-subagents attempts launch
- **THEN** it MUST refuse that provider-specific request rather than silently use a same-named model from another provider
- **AND** a source release note alone MUST NOT count as observed model-family diversity

#### Scenario: drain-aware stop and multi-session lifecycle
- **GIVEN** an upgraded Pi-subagents workflow has active and queued children
- **WHEN** `stop` with `drain:true` is exercised
- **THEN** new child dispatch MUST stop, running children MAY settle and preserve their results
- **AND** no cancelled/stopped workflow or another session's child MAY be counted as an accepted independent reviewer without terminal evidence

### Requirement: Pi package resources and role semantics must be separate verifiable contracts
A future Pi package MUST derive its native manifest version and IDs from canonical `pstack.package.json`, exposing `pi.skills: ["./skills"]` and `pi.subagents.agents: ["./agents"]` without bundling third-party code. Native package install and extension role lookup MUST be independently observed. Child tool permissions, thinking parameters, and read-only limits MUST be verified explicitly.

#### Scenario: Pi-native package exposes roles without copying agents
- **GIVEN** 22 canonical PStack `roles[].id` and a proposed `package.json` with both `pi.skills` and `pi.subagents.agents`
- **WHEN** a disposable trusted project installs that exact package with an independently installed pi-subagents extension
- **THEN** PStack skill names and all 22 role identities MUST be discoverable without parallel handwritten role trees
- **AND** a discovery failure, disabled extension or duplicate legacy package MUST remain PACKAGE GAP

#### Scenario: Generic role effort and skill context do not map automatically
- **GIVEN** a canonical role uses `effort: xhigh` or asks to read PStack principles
- **WHEN** pi-subagents loads the source role as a fresh child
- **THEN** PStack MUST NOT infer `thinking: xhigh` or inherited skills from the mere existence of the role file
- **AND** explicit host-local setting/override or source-derived projection MUST be tested before claiming semantic parity

#### Scenario: Independent verifier has prompt-only readonly instruction
- **GIVEN** `agents/independent-verifier.md` says not to edit, but its Pi-native tool allowlist and OS sandbox have not been proven
- **WHEN** a review child starts with default Pi tools
- **THEN** the verifier's hard-readonly enforcement MUST remain UNVERIFIED/BLOCKED
- **AND** a negative native write/bash test MUST prove the effective tool/OS restriction before any isolated reviewer PASS

#### Scenario: Core delegation works without optional guarded extensions
- **GIVEN** Pi built-ins and exactly one pi-subagents delegation engine, but no pi-ask-user, pi-verdict or pi-better-sandbox
- **WHEN** a read-only/nonprivileged PStack swarm/arena operation is requested
- **THEN** it MAY use the delegate engine subject to native role/child/runtime proof
- **AND** structured human.ask, guarded OS confinement and hard human.gate remain individually GAP/BLOCKED rather than falsely presented as included

### Requirement: Pi authorization and formal verification must not overclaim their enforcement
A pi-verdict hook MAY reject unsafe calls, but classifier approval is not sufficient to prove mandatory human.gate or OS sandbox enforcement. Missing hooks or unverified child actions MUST remain fail-closed. Verification skills MUST distinguish finite source-contract tests from native formal verification and checker availability.

#### Scenario: classifier allow but hard action lacks authorization
- **GIVEN** an attempted privileged child/custom tool action returns `allow` from pi-verdict but no independently enforced human permission
- **WHEN** the runtime verifier observes effect authorization
- **THEN** it MUST reject a hard-gate PASS claim
- **AND** this PStack Pi candidate MUST retain `human.gate` as GAP

#### Scenario: source mutant tests pass but native checker never runs
- **GIVEN** all 53 finite invalid contract variants are rejected
- **WHEN** `verify-pi-pstack-formal` is evaluated without a real code-linked model checker or native transition proof
- **THEN** it MAY report bounded source-contract PASS only
- **AND** native formal/security proof MUST remain NOT_RUN/BLOCKED

### Requirement: PStack Pi package reuse does not invert upstream or downstream authority
Canonical PStack skills MUST preserve the applied Cursor intent and remain independently usable without Pi or QStack. Pi is an optional host projection; QStack `qstack-mode` may consume independently installed `poteto-mode`, but PStack MUST NOT import QStack, invent a new execution engine or add a model/provider registry to accommodate the Pi package.

#### Scenario: PStack skills loaded in a Pi-free or QStack-free environment
- **GIVEN** a host installs canonical PStack with neither Pi extensions nor QStack
- **WHEN** a normal PStack skill or playbook is invoked on its supported host
- **THEN** upstream PStack semantic behavior and role contracts MUST remain available
- **AND** no Pi-specific package module, quant overlay or additional controller is required

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
