## ADDED Requirements

### Requirement: Grok remaps are opt-in copies, not plugin hooks

Feature: benny-grok-remap

The grok port MUST keep Cursor `/automate` and `.cursor/automations/` as source documentation only. Live grok copies MUST live under `automations/benny/grok/`. Operators MUST copy hooks into a target `.grok/hooks/` and workflows into `.grok/workflows/`. pstack `plugin.json` MUST NOT grow a `hooks` key, because plugin hooks would run for every pstack user. Slack channel auto-start MUST be documented as a host gap. Attended runs use `/workflow benny-triage` or `/workflow benny-repro` with `args.thread_url`. Overnight waits use `/loop` → `scheduler_create`. Fail-closed merge and force-push MUST be a `PreToolUse` command hook in the copied pack.

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
- **AND** source-channel `thread_ts` remains prompt-enforced in `SKILL.md` and the workflow prompt
- **AND** grok has no Slack channel auto-start
