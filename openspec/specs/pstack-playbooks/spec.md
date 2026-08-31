# pstack-playbooks Specification

## Purpose
TBD - created by archiving change pstack-atomic-blocks. Update Purpose after archive.

## Requirements

### Requirement: Twenty-two named playbooks plus opening-a-pr

Feature: pstack-playbooks

The plugin MUST ship the official playbook set under `skills/poteto-mode/playbooks/`: investigation, bug-fix, perf-issue, hillclimb, runtime-forensics, trace-forensics, feature, refactoring, prototype, visual-parity, authoring-a-skill, eval, babysit, shipping, autonomous-run, orchestrate, autopilot-full, autopilot-stack, session-pickup, pause-safely, multi-phase-plan, worktree-cleanup, plus `opening-a-pr.md` invoked at the end of other playbooks.

#### Scenario: inventories match official pin

- **GIVEN** official pstack at UPSTREAM `tree` pin
- **WHEN** playbook filenames are listed
- **THEN** this port has the same 23 markdown files

`make-bot-ui` is a **skill**, not a playbook. This port MUST NOT ship `skills/make-bot-ui`. No-match / large work routes to `/figure-it-out` (`skills/figure-it-out/SKILL.md`), not a playbook file.
