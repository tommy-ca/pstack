## ADDED Requirements

### Requirement: Grok remaps are opt-in copies, not plugin hooks

Feature: benny-grok-remap

Official and Cursor Benny under `automations/benny/skills/` is the **upstream reference** for intent and atomic blocks only. It is not the live grok operational contract. Live grok instructions MUST live under `automations/benny/grok/` (`triage.md`, `repro.md`, workflows, opt-in hooks). They MUST name grok-build natives: `spawn_subagent` with `pstack:<role>`, `args.thread_url`, `/loop` → `scheduler_create`, copied `PreToolUse` hooks. They MUST NOT tell a run to follow Cursor `/automate`, `trigger.thread_ts`/`trigger.ts`, or `.cursor/automations/` as the live path. Operators MUST copy hooks into a target `.grok/hooks/` and workflows into `.grok/workflows/`. pstack `plugin.json` MUST NOT grow a `hooks` key. Slack channel auto-start MUST stay a host gap.

#### Scenario: opt-in layout

- **GIVEN** this port's tree
- **WHEN** an operator wants grok-native Benny
- **THEN** `automations/benny/grok/README.md` names copy targets `.grok/hooks/` and `.grok/workflows/`
- **AND** it names `scheduler_create`
- **AND** it does not tell them to run Cursor `/automate`
- **AND** `plugin.json` still has no `hooks` key

#### Scenario: fail-closed hook denies merge

- **GIVEN** the copied `automations/benny/grok/hooks/hooks.json` in a trusted target
- **WHEN** the agent is about to run `gh pr merge` or `git push --force`
- **THEN** the `PreToolUse` hook returns deny

#### Scenario: Slack thread_ts stays prompt-enforced

- **GIVEN** `automations/benny/grok/bin/fail-closed.sh`
- **WHEN** the tool command is not merge or force-push
- **THEN** the script returns allow
- **AND** source-channel freeze is prompt-enforced in grok `triage.md` / `repro.md` from `args.thread_url`
- **AND** grok has no Slack channel auto-start

#### Scenario: live grok path does not follow Cursor SKILL.md

- **GIVEN** `automations/benny/grok/workflows/benny-triage.rhai` and `benny-repro.rhai`
- **WHEN** a run starts
- **THEN** the workflow reads grok `triage.md` or `repro.md`
- **AND** it does not instruct following `automations/benny/skills/*/SKILL.md` as the live coordinator
- **AND** those grok files name `spawn_subagent` and `pstack:<role>`
