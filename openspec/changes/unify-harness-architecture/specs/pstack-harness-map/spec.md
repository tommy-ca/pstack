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
