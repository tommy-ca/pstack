# pstack-portability: reference-port delta contract

## ADDED Requirements

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
