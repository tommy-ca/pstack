# pstack-agent-orchestration: portable policy/execution boundary

## ADDED Requirements

### Requirement AO-R01: PStack remains the single development policy authority
PStack orchestration MUST own software task readiness, dependencies, worktree/branch/PR policy and acceptance. External executors MAY own their own runtime child and placement state, but MUST NOT become a second authoritative development graph. QStack's research graph MUST remain separate and downstream.

#### Scenario: External executor proposes an independent task completion
- **GIVEN** a PStack development work unit with an open verification gate
- **WHEN** an executor reports that its child has finished
- **THEN** PStack MUST keep the unit unaccepted until the PStack predicate is proven
- **AND** the executor's task state MUST NOT overwrite PStack graph state

### Requirement AO-R02: Every effect is bound to a stable request identity
Every dispatched effect MUST correlate `ownerId`, `invocationId`, `requestId` and `executionId`. A retry of an identical request MUST re-observe or return its original receipt; the same `requestId` with changed essential arguments MUST refuse as a conflict.

#### Scenario: Retried launch with changed payload
- **GIVEN** request `r` already prepared for task `t1` on `main`
- **WHEN** the caller retries `r` with task `t2` or a different branch
- **THEN** the adapter MUST refuse with an explicit identity conflict
- **AND** no second agent or job MAY be launched

### Requirement AO-R03: Observation is read-only
Observing, polling, resuming or reconciling execution state MUST NOT implicitly create another launch. A timeout or lost receipt MUST be represented as uncertainty until runtime evidence proves otherwise.

#### Scenario: Launch effect happened but response was lost
- **GIVEN** a child started and its launch RPC timed out before returning a receipt
- **WHEN** the caller retries observation
- **THEN** the adapter MUST NOT issue another launch
- **AND** the result MUST remain `unresolved` unless correlated evidence resolves it

### Requirement AO-R04: A child turn or answer is not terminal proof
A successful child answer, ended terminal turn, closed pane, captured transcript or process exit alone MUST NOT imply a fulfilled task. A passing execution MUST bind a terminal proof to the exact execution incarnation, source revision and task acceptance criterion.

#### Scenario: Prose-only success
- **GIVEN** a child replies "done" without terminal acceptance evidence
- **WHEN** PStack evaluates completion
- **THEN** the verdict MUST be `UNTESTED` or `BLOCKED`, never `PASS`
- **AND** the task MUST remain unaccepted

#### Scenario: Receipt belongs to a different execution
- **GIVEN** evidence for `execution-1` at revision `a`
- **WHEN** `execution-2` at revision `b` attempts to reuse it
- **THEN** the verifier MUST reject the evidence as inapplicable
- **AND** it MUST NOT satisfy the gate

### Requirement AO-R05: Cancellation and timeout fence late success
Once cancellation is accepted, late callbacks and child messages MUST NOT turn the cancelled execution into success. A child with unknown, cancelled, timed-out or lost execution evidence cannot satisfy PASS.

#### Scenario: Late completion after cancellation
- **GIVEN** execution `e` was cancelled before its child completed
- **WHEN** its delayed success callback arrives
- **THEN** the execution MUST remain cancelled for acceptance
- **AND** the callback MAY be retained as evidence but MUST NOT change the parent's verdict to PASS

### Requirement AO-R06: Parent closure is gated on owned children
An orchestrator MUST preserve ownership of pending, asking, blocked, unknown and unresolved children. Parent completion MUST be refused until owned children settle or are explicitly and safely handed off.

#### Scenario: Parent declares completion with a pending child
- **GIVEN** a parent owns one unreturned child
- **WHEN** the parent requests completion
- **THEN** completion MUST be refused with the child identity
- **AND** no child resource MAY be silently abandoned

### Requirement AO-R07: Resource cleanup must protect uncertain and dirty workspaces
A workspace owner MUST NOT delete or reuse an assigned worktree while pending ownership, dirty/untracked data, or uncertain preservation exists. Preservation must be demonstrated before destructive cleanup.

#### Scenario: Orphaned worker left an untracked file
- **GIVEN** a lost worker owns a checkout containing untracked work
- **WHEN** cleanup executes
- **THEN** cleanup MUST preserve work through a verified recovery artifact or refuse
- **AND** no unsafe deletion MAY be reported as successful

### Requirement AO-R08: Capability and security boundaries fail closed
Host adapter selection MUST derive executable capability from the active host profile and observed installed tooling. Unsupported, denied or ambiguous send/spawn/cancel/observe routes MUST produce `BLOCKED` or explicit failure, not a guessed CLI call or screen-paste fallback.

#### Scenario: An optional executor is not installed
- **GIVEN** a task requests a Mu or Dogsled executor not proven on the current host
- **WHEN** capability discovery runs
- **THEN** dispatch MUST NOT begin
- **AND** the report MUST say `BLOCKED` with missing capability evidence

### Requirement AO-R09: Parallel workers are individually accountable
Swarm MUST cover disjoint slices or predeclared race arms; arena MUST run the identical frozen brief and rubric per independent candidate; interrogate MUST record each reviewer's actual identity and independently reproduce findings. Missing/dropped/cancelled lanes MUST remain gaps and MUST NOT be counted as a successful completed lane.

#### Scenario: An arena reports one reused agent as three independent judges
- **GIVEN** only one observed worker incarnation ran three successive prompts
- **WHEN** the report claims three independent candidate seats
- **THEN** the report MUST reject independent-seat evidence
- **AND** it MUST name the context reuse or missing arms as a gap

### Requirement AO-R10: Verification evidence levels are not interchangeable
Static structure, offline tests, bounded model checks and observed live conformance MUST have distinct labels. Unavailable checker, missing live runtime, absent negative mutant, or unobserved user path MUST NOT be promoted to a passing runtime verdict.

#### Scenario: Model checker unavailable
- **GIVEN** the project model requires TLC and Java/TLC cannot be executed
- **WHEN** a review requests formal verification
- **THEN** the formal check MUST report `BLOCKED`
- **AND** a static inspection MAY be reported separately, never as model-checked PASS

### Requirement AO-R11: Source-linked formal claims require a falsifier
Each formal invariant MUST identify concrete target functions and atomic transitions, state its assumptions and bounds, and include a reachable mutant that breaks the invariant. Safety and conditional liveness MUST be reported separately; no model transferred from Mu/Dogsled counts as a native PStack proof.

#### Scenario: A copied model passes but has no target mapping
- **GIVEN** a source-port TLA+ model passes on its own assumptions
- **WHEN** no target code action maps to its atomic steps
- **THEN** the model MUST be labeled reference-only or `UNTESTED`
- **AND** the PStack target invariant MUST remain unproven

### Requirement AO-R12: Source pinning and directed dependency are mandatory
Adopted concepts MUST cite exact upstream source revisions and owner boundaries. PStack MUST NOT import QStack, while QStack MAY depend on its independently installed PStack capabilities. Source imports or licenses must be reviewed separately from conceptual paraphrase.

#### Scenario: PStack orchestration calls qorch
- **GIVEN** a PStack-only software workflow with no QStack installed
- **WHEN** PStack resolves task readiness or agent dispatch
- **THEN** it MUST work without QStack
- **AND** importing a QStack runtime module MUST fail architectural review

## Applicability

These are **candidate contracts** for an opt-in executor and for review/verification of existing orchestration paths. They do not assert existing PStack implementations conform. AO-04 requires code-linked tests and observed runtime receipts before any new adapter is shipped.
