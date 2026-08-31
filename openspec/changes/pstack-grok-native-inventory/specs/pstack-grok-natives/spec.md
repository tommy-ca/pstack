## ADDED Requirements

### Requirement: Inventory grok natives with an adopt/skip/gap plan

Feature: pstack-grok-natives

Operator docs MUST list grok CLI and slash natives that pstack does not wrap. Each row MUST be adopt, skip, or gap. Docs MUST name `grok --worktree`, `grok -p`, and `enter_plan_mode`. They MUST NOT add plugin `commands/` clones of `/plan` or `/goal`.

#### Scenario: guide names CLI and plan tool

- **GIVEN** `docs/guide/13-grok-natives.md`
- **WHEN** an operator asks what grok can do that playbooks omit
- **THEN** the page names `grok --worktree`, `grok -p`, and `enter_plan_mode`
- **AND** it uses skip for `/plan` clones and plugin `hooks`
