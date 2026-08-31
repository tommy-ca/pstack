# benny-triage Specification

## Purpose

Keep Benny triage thread-only, marker-based, duplicate-aware, and fail-closed when configuration is incomplete.

## Requirements

### Requirement: Triage posts one thread-only verdict

Feature: benny-triage

Triage MUST freeze source channel and root thread coordinates before any write. It MUST classify the report, search the tracker for duplicates, and create a ticket only for a clear net-new bug or performance issue. It MUST post exactly one reply in the source thread. The reply MUST end with one configured marker: `[benny:bug]`, `[benny:performance]`, or `[benny:other]`. A bug or performance marker MAY include `tracker=<url>`. It MUST NOT post a source-channel root message.

#### Scenario: marker contract

- **GIVEN** a classified Slack report in the configured source channel
- **WHEN** triage finishes
- **THEN** the source thread contains exactly one new reply from the triage identity
- **AND** that reply contains exactly one of `[benny:bug]`, `[benny:performance]`, or `[benny:other]`
- **AND** no root message was posted in the source channel

#### Scenario: fail closed on missing config

- **GIVEN** missing, malformed, or incomplete Benny configuration
- **WHEN** triage starts
- **THEN** it posts nothing
- **AND** it writes nothing to the tracker
