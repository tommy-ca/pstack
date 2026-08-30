## ADDED Requirements

### Requirement: Cursor harness calls map to grok natives

Feature: pstack-harness-map

Playbook **intent** stays. Call sites MUST use grok natives from `HARNESS.md`: `spawn_subagent` (alias `task`) not Cursor `Task`; `ask_user_question` not `AskQuestion`; `/loop` expands to `scheduler_create` (min 60s, new turn) not Cursor same-run `/loop`; `monitor` for watch predicates. Child `subagent_type` MUST be `pstack:<role-key>`. `MAX_SUBAGENT_DEPTH` is 1; the parent fans out.

#### Scenario: spawn type

- **GIVEN** a feature playbook spawn
- **WHEN** the parent calls `spawn_subagent`
- **THEN** `subagent_type` is `pstack:feature`
- **AND** `reasoning_effort` is not sent on the wire
