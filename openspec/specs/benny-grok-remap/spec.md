# benny-grok-remap Specification

## Purpose

Define the opt-in, plugin-installed Grok Benny path while retaining the Cursor
Benny tree as upstream reference material.

## Requirements

### Requirement: Grok remaps are plugin-installed, not copied hooks

Feature: benny-grok-remap

Official and Cursor Benny under `automations/benny/skills/` is the **upstream
reference** for intent and atomic blocks only. It is not the live grok
operational contract. Live grok instructions MUST live under
`automations/benny-grok/` (sibling of the Cursor pack), as `/benny-triage` and
`/benny-repro` loaded from `plugin.json` `skills`. After `grok plugin enable
pstack` they MUST be invocable with no copy into `.grok/hooks` or
`.grok/workflows`. They MUST name grok-build natives: `spawn_subagent` with
`pstack:<role>`, permalink / `args.thread_url`, `/loop` →
`scheduler_create`. They MUST NOT tell a run to follow Cursor `/automate`,
`trigger.thread_ts`/`trigger.ts`, or `.cursor/automations/` as the live path.
pstack `plugin.json` MUST NOT grow a `hooks` key. The merge-deny script MUST
NOT run for every pstack user. Slack channel auto-start MUST stay a host gap.

#### Scenario: opt-in layout

- **GIVEN** this port's tree
- **WHEN** an operator enables pstack
- **THEN** `automations/benny-grok/README.md` names `grok plugin enable pstack`
- **AND** it does not name `mkdir -p .grok/hooks` as the install path
- **AND** it names `scheduler_create`
- **AND** `plugin.json` still has no `hooks` key
- **AND** `plugin.json` `skills` includes `./automations/benny-grok/skills/`

#### Scenario: fail-closed hook is not plugin-global

- **GIVEN** `automations/benny-grok/bin/fail-closed.sh`
- **WHEN** the agent is about to run `gh pr merge`, `git push --force`, or a
compound `git merge` followed by a plain `git push` **and** the operator has
installed that script as a project hook
- **THEN** the script returns deny
- **AND** `plugin.json` does not register that hook

#### Scenario: Slack freeze stays prompt-enforced

- **GIVEN** `automations/benny-grok/bin/fail-closed.sh`
- **WHEN** the tool command is not merge or force-push
- **THEN** the script returns allow
- **AND** source-channel freeze is prompt-enforced in grok `benny-triage` /
`benny-repro` skills
- **AND** grok has no Slack channel auto-start

#### Scenario: live grok path does not follow Cursor SKILL.md

- **GIVEN** `automations/benny-grok/skills/benny-triage/SKILL.md` and `benny-repro/SKILL.md`
- **WHEN** a run starts
- **THEN** those files are the live coordinators
- **AND** they do not instruct following
`automations/benny/skills/*/SKILL.md` as the live coordinator
- **AND** they name `spawn_subagent` and `pstack:<role>`
