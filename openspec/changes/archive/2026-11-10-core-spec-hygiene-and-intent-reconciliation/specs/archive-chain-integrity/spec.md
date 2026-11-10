# archive-chain-integrity — Specification hygiene and validation tightening

## MODIFIED Requirements

### Requirement: Archived intent-driven changes retain the full chain
Every completed archived OpenSpec change MUST contain proposal.md, at least one specification under specs/, design.md, adr.md, tasks.md, and .openspec.yaml. The integrity check MUST inspect every archive directory and fail with any missing artifact paths. Each task checkbox MUST have a closed outcome. External operations that cannot be proven locally MAY close with an explicit deferred outcome annotation naming the reason and follow-up without claiming execution.

#### Scenario: Complete archived chains pass
- **GIVEN** an archive directory containing proposal, specification, design, ADR review, tasks, and metadata files
- **AND** every task has either execution evidence or a truthful deferred outcome annotation
- **WHEN** the archive integrity check runs
- **THEN** that archive passes
- **AND** the check continues to inspect every other archive

#### Scenario: Missing historical artifacts fail closed
- **GIVEN** an archived change whose tasks are complete but whose design or ADR file is missing
- **WHEN** the archive integrity check runs
- **THEN** the check fails with the archive name and each missing artifact
- **AND** checked task boxes do not conceal the missing intent artifacts

#### Scenario: Historical content is not rewritten
- **GIVEN** a repair adds missing artifacts or closes an externally blocked task with an outcome annotation
- **WHEN** the repaired archive is reviewed
- **THEN** its original proposal, specifications, design, ADR, and task intent remain reviewable
- **AND** any deferred annotation states the unavailable action, reason, and follow-up without claiming execution

#### Scenario: External work stays visibly deferred
- **GIVEN** a release task requires a sibling marketplace checkout or a host-side plugin update
- **WHEN** that external operation is not authorized or cannot be proven locally
- **THEN** the archived task records the operation as deferred
- **AND** the record names the sibling checkout or host surface needed for follow-up
- **AND** strict archive validation does not report the task as unchecked
