# Delta specification: source-pinned cross-port semantic parity

The requirements below extend, not replace, openspec/specs/pstack-portability/spec.md and the existing create-/maintain-verification-skill, evidence and wiki contracts.

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
