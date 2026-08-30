## ADDED Requirements

### Requirement: Benny files are dormant source, not slash skills

Feature: benny-pack

The pack MUST live under `automations/benny/`. Cursor `SKILL.md` files there are the **upstream reference** (intent and atomic blocks). They MUST NOT appear in `plugin.json` `skills` and MUST NOT exist under plugin `skills/`. They MUST NOT be the live grok coordinator. User-owned configuration, feature maps, routing maps, and secrets MUST live outside the pack so a refresh cannot overwrite them.

#### Scenario: plugin manifest ignores the pack

- **GIVEN** `plugin.json` on this port
- **WHEN** skills and hooks keys are read
- **THEN** `skills` includes `./skills/` and `./automations/benny-grok/skills/`
- **AND** `hooks` is absent
- **AND** the Cursor pack directory is not itself a skill path
- **AND** `skills/setup-benny`, `skills/triage-issue-reports`, and `skills/reproduce-and-fix-issues` do not exist

#### Scenario: user config is outside the pack

- **GIVEN** a target repository using Benny
- **WHEN** configuration, feature map, or routing map is stored
- **THEN** those files are outside `automations/benny/`
- **AND** pack refresh does not overwrite them
