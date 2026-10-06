## MODIFIED Requirements

### Requirement: Grok maps portable capabilities to Grok-native primitives

Feature: pstack-harness-map

Grok-specific call sites MUST follow `skills/poteto-mode/references/grok-tools.md`. Playbook intent stays canonical. The adapter maps portable capabilities to Grok-native spawn, join, question, progress, isolation, monitoring, and scheduling behavior.

Examples include `spawn_subagent` / wire alias `task`, `get_command_or_subagent_output`, `ask_user_question`, `todo_write`, worktree isolation, `monitor`, and `scheduler_create`.

These names MUST NOT become the portable vocabulary used to specify Codex, Claude Code, or future hosts.

#### Scenario: feature writer

- **GIVEN** the Feature playbook requires a writer
- **WHEN** the Grok adapter executes it
- **THEN** the parent uses the Grok spawn primitive with the mapped pstack role
- **AND** host-invalid Cursor fields are not sent
- **AND** required postconditions come from the portable capability contract, not from the Grok field names

### Requirement: Grok depth limits alter topology, not playbook intent

Feature: pstack-harness-map

Grok's depth-one subagent limit MUST be handled by parent-owned fan-out. The adapter MAY change where spawn occurs, but MUST preserve required independence, fan-out, joining, and verification.

#### Scenario: parent-owned depth-one fan-out

- **GIVEN** a playbook fans out independent collaborators
- **WHEN** the Grok adapter spawns them
- **THEN** the parent owns the fan-out within the depth-one limit
- **AND** required independence, fan-out, joining, and verification are preserved even when spawn moves

### Requirement: Grok static checks are adapter checks

Feature: pstack-harness-map

`scripts/verify-harness.py`, plugin validation, and Grok manifest checks MAY prove static adapter conformance. They MUST NOT by themselves establish runtime conformance or universal pstack portability.

#### Scenario: static checks stay adapter-scoped

- **GIVEN** `scripts/verify-harness.py`, plugin validation, and Grok manifest checks pass
- **WHEN** conformance is claimed from them
- **THEN** the claim is limited to static adapter conformance
- **AND** no runtime conformance or universal pstack portability is inferred from static checks alone
