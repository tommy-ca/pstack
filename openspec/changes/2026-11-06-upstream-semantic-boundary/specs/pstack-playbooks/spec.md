# pstack-playbooks: preserve review and coordination semantics

## ADDED Requirements

### Requirement: Orchestrate remains a playbook and not an engine
The canonical orchestrate playbook MUST retain its coordination *intent* (briefs, scoped ownership, predicates, host state, verification, and honest gaps). The port MUST map unsupported host mechanisms to explicit gaps; it MUST NOT implement a parallel Mu/Dogsled engine to satisfy the playbook.

#### Scenario: Host cannot observe a nested subagent
- **GIVEN** canonical playbook intent requires nested ownership and terminal join
- **WHEN** the ported host lacks proven support
- **THEN** the port MUST report a semantic capability gap
- **AND** it MUST NOT fabricate a passing join or introduce a second scheduler

### Requirement: Swarm accounts for independent coverage
Swarm MUST define slices or race arms, require separately attributable evidence, and report dropped/unproven work as gaps.

#### Scenario: Required lane absent
- **GIVEN** three independent slices are required
- **WHEN** only two return verifiable reports
- **THEN** the missing slice MUST remain a coverage gap
- **AND** aggregate PASS MUST NOT imply full coverage

### Requirement: Arena evaluates the same task before synthesis
Arena MUST use a frozen candidate brief, declared rubric and isolated outputs. Cross-family judges MUST be described as run only when there is observed judge evidence; otherwise a skip MUST be stated.

#### Scenario: No independent judge available
- **GIVEN** candidates have completed
- **WHEN** no supported independent judge can run
- **THEN** synthesis MAY proceed using the declared rubric
- **AND** the report MUST name the skipped judge rather than claim a panel verdict

### Requirement: Interrogate retains only demonstrated failures
Interrogate MUST challenge the scoped diff or design and rerun evidence for each retained finding. Unexecuted hypotheses MUST NOT be promoted to verified defects.

#### Scenario: Reviewer suggests a speculative defect
- **GIVEN** a reviewer gives a plausible failure mode without a runnable reproduction
- **WHEN** an interrogate report is consolidated
- **THEN** the claim MUST be dropped or explicitly unverified
- **AND** it MUST NOT be counted as a confirmed finding

### Requirement: Quality-review methods do not change runtime ownership
Thermo-Nuclear correctness and code-quality reviews MUST focus on the changed diff, preserve host/semantic boundaries, and prefer deletion of speculative abstractions. Review workflow composition MUST NOT itself become an execution protocol.

#### Scenario: Review asks for a generic dispatch framework
- **GIVEN** a source-only PStack semantics PR
- **WHEN** a suggested improvement introduces generic executor plumbing
- **THEN** the reviewer MUST reject it under scope discipline and YAGNI
- **AND** may retain a source-attributed prior-art note
