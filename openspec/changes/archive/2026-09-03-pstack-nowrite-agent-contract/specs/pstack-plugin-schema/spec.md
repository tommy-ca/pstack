## ADDED Requirements

### Requirement: No-write plugin agents use capabilityMode execute

Feature: pstack-plugin-schema
Rule: closed no-write set vs everyone else

Grok 1.0.13 applies `AgentDefinition.capabilityMode`. Mode `execute` allows read and shell and forbids file edits. Spawn `capability_mode` is ignored.

The no-write set is exactly `how-explorer`, `how-explainer`, `how-critics`, `interrogate-reviewers`, `arena-cross-judge-pool`, `independent-verifier`, and `comment-sicko`. Each of those agent files MUST set `capabilityMode: execute`. Every other `agents/*.md` file MUST omit `capabilityMode`. `why-investigators`, `why-synthesizer`, `reflect-judgment`, and `reflect-tooling` stay prompt posture. `inheritSkills` is not part of this write-bit contract.

#### Scenario: no-write agents keep execute

- **GIVEN** the seven no-write agent files exist
- **WHEN** the verification test reads their YAML frontmatter
- **THEN** each file contains `capabilityMode: execute`
- **AND** a missing or different mode on any of those files fails the test with the agent path

#### Scenario: writers and prompt-posture agents omit capabilityMode

- **GIVEN** every other file under `agents/`
- **WHEN** the verification test reads their YAML frontmatter
- **THEN** `capabilityMode` is absent
- **AND** an accidental `capabilityMode: execute` on a writer or prompt-posture agent fails the test with the agent path
