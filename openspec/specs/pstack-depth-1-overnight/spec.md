# pstack-depth-1-overnight Specification

## Purpose
Grok Build `MAX_SUBAGENT_DEPTH` is 1. Autopilot queue playbooks must parent-fanout, spawn `pstack:comment-sicko` after writers join, and must not arm `/goal`.

## Requirements

### Requirement: Autopilot playbooks parent-fanout and skip /goal

Feature: pstack-depth-1-overnight

On Grok Build, `MAX_SUBAGENT_DEPTH` is 1. `autopilot-full.md` and `autopilot-stack.md` MUST tell the parent session to own every `spawn_subagent` call, including `pstack:comment-sicko` after a writer joins. Writer children MUST NOT invoke `/no-comments` (that skill spawns). They MUST NOT arm `/goal`. Heartbeat stays `/loop` → `scheduler_create`. Event wakes stay `monitor`.

#### Scenario: no nested comment-sicko from writers

- **GIVEN** `skills/poteto-mode/playbooks/autopilot-full.md` and `autopilot-stack.md`
- **WHEN** a writer child finishes a PR
- **THEN** the playbook names `MAX_SUBAGENT_DEPTH`
- **AND** the parent spawns `pstack:comment-sicko`
- **AND** the playbook does not arm a `/goal`
