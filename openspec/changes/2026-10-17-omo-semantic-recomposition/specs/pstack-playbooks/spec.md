# pstack-playbooks delta: OmO-inspired runtime composition

## ADDED Requirements

### Requirement: Principle, leaf skill and workflow responsibilities remain distinct
An OmO semantic block MUST NOT be presented as a new canonical principle or playbook when pinned upstream already supplies the decision rule or workflow. Canonical cross-cutting principles constrain implementation; leaf skills produce bounded engineering outputs; compositions sequence skills and host capabilities.

#### Scenario: recovery behavior extracted from OmO
- **GIVEN** OmO provides run fencing and uncertain-delivery handling
- **WHEN** the port records their reusable lessons
- **THEN** it maps them to canonical idempotency, boundary, model-the-domain and verification principles
- **AND** implements them as host-owned execution contracts rather than a new portable recovery engine.

### Requirement: Swarm coverage accounts for all declared partitions
Swarm MUST freeze a coverage or race selection rule before dispatch. Every required partition MUST finish with valid evidence or an explicit gap/dropout; a missing required result MUST NOT be counted as PASS.

#### Scenario: one required worker drops out
- **GIVEN** a coverage Swarm declares three required slices
- **WHEN** one worker never produces a valid receipt
- **THEN** aggregate coverage reports the missing slice
- **AND** the complete-coverage predicate does not pass.

### Requirement: Arena maintains artifact and reviewer independence
Arena MUST freeze rubric before generation, place independent candidates in separate writable contexts, judge only completed candidates, select and graft a coherent base, and verify the post-graft artifact. A warmed shared worker context MUST NOT be claimed as independent.

#### Scenario: reused Workpool reviewer
- **GIVEN** a native Workpool schedules two Arena candidates into the same residual context
- **WHEN** an adapter evaluates independence
- **THEN** it refuses the independent-candidate claim
- **AND** records adaptation/gap rather than fabricated multi-agent parity.

### Requirement: Interrogate retains reviewer independence without automatic mutation
Interrogate MUST give independent reviewers an identical review pack, preserve disagreements and lead dispositions, and MUST NOT auto-apply code changes. Native read-only enforcement MUST be distinguished from prompt-only advisory restrictions.

#### Scenario: review findings request fixes
- **GIVEN** reviewer outputs propose changes
- **WHEN** the lead synthesizes the report
- **THEN** findings are triaged into explicit dispositions
- **AND** implementation changes require separately owned work rather than reviewer auto-edits.

### Requirement: Long-horizon program completion uses fresh verification
Orchestrate MUST retain standing orders in each new brief, drain completions as queue events, preserve a rolling verified frontier and reconcile context/session rollover. Work completion MUST be tied to the program's unchanged acceptance predicate and current artifact evidence.

#### Scenario: agent response succeeded but artifact changed
- **GIVEN** a worker returned success and an old revision passed checks
- **WHEN** the artifact digest or relevant integration base changes
- **THEN** the previous passing evidence is invalidated where affected
- **AND** the host cannot complete the program on the worker report alone.
