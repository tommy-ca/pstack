## ADDED Requirements

### Requirement: Repro waits for a trusted marker then proves the symptom twice

Feature: benny-repro

Repro MUST wait for a trusted triage marker in the frozen source thread. It MUST proceed only for `bug` or `performance` from the configured triage identity. It MUST reproduce the discriminating symptom twice through the real UI via the configured control adapter. It MUST NOT treat a unit test, screenshot of source, or injected state as a repro. An existing pull request or merged commit MUST switch the run to verify mode. A bounded fix MAY open a **draft** pull request only after before-and-after UI proof. It MUST NOT merge or deploy.

#### Scenario: untrusted or other marker stops the run

- **GIVEN** a source thread whose only marker is `[benny:other]`, missing, or from an untrusted author
- **WHEN** repro waits for the verdict budget
- **THEN** it authors no diff
- **AND** it posts no source-channel root message

#### Scenario: draft only after proof

- **GIVEN** a confirmed twice-reproduced bug, no existing fix artifact, and no person claiming the fix
- **WHEN** before-and-after UI proof passes
- **THEN** the run may open a draft pull request
- **AND** it does not merge or deploy
