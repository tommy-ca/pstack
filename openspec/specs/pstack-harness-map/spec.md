# pstack-harness-map Specification

## Purpose

Define the Grok Build reference-adapter mapping. This legacy spec name is Grok-scoped; the cross-harness contract lives in `pstack-portability`.

## Requirements

### Requirement: Grok maps portable capabilities to Grok-native primitives

Feature: pstack-harness-map

Grok-specific call sites MUST follow `HARNESS.md`. Playbook intent stays canonical. The adapter maps portable capabilities to Grok-native spawn, join, question, progress, isolation, monitoring, and scheduling behavior.

Examples include `spawn_subagent` / wire alias `task`, `get_command_or_subagent_output`, `ask_user_question`, `todo_write`, worktree isolation, `monitor`, and `scheduler_create`.

These names MUST NOT become the portable vocabulary used to specify Codex, Claude Code, or future hosts.

#### Scenario: feature writer

- **GIVEN** the Feature playbook requires a writer
- **WHEN** the Grok adapter executes it
- **THEN** the parent uses the Grok spawn primitive with the mapped pstack role
- **AND** host-invalid Cursor fields are not sent
- **AND** required postconditions come from the portable capability contract, not from the Grok field names

### Requirement: Grok depth limits alter topology, not playbook intent

Grok's depth-one subagent limit MUST be handled by parent-owned fan-out. The adapter MAY change where spawn occurs, but MUST preserve required independence, fan-out, joining, and verification.

### Requirement: Grok static checks are adapter checks

`scripts/verify-harness.py`, plugin validation, and Grok manifest checks MAY prove static adapter conformance. They MUST NOT by themselves establish runtime conformance or universal pstack portability.
