# archive-chain-integrity Specification

## Purpose

Ensure archived OpenSpec changes retain a complete, reviewable
intent-driven artifact chain.

## Requirements

### Requirement: Archived intent-driven changes retain the full chain

Every completed archived OpenSpec change MUST contain `proposal.md`, at least
one Markdown specification under `specs/`, `design.md`, `adr.md`, `tasks.md`,
and `.openspec.yaml`. The integrity check MUST inspect every immediate archive
directory and MUST fail with the missing artifact paths.

#### Scenario: Complete archived chains pass

- **GIVEN** an archive directory containing proposal, specification, design,
ADR review, tasks, and metadata files
- **WHEN** the archive integrity check runs
- **THEN** that archive passes
- **AND** the check continues to inspect every other archive

#### Scenario: Missing historical artifacts fail closed

- **GIVEN** an archived change whose tasks are complete but whose design or ADR
file is missing
- **WHEN** the archive integrity check runs
- **THEN** the check fails with the archive name and each missing artifact
- **AND** checked task boxes do not conceal the missing intent artifacts

#### Scenario: Historical content is not rewritten

- **GIVEN** a repair adds missing artifacts to an existing archive
- **WHEN** the repaired archive is reviewed
- **THEN** its original proposal, specs, tasks, and metadata remain unchanged
- **AND** the new design/ADR files identify themselves as retrospective chain repairs
