## ADDED Requirements

### Requirement: Source coordinates stay immutable and workers cannot post

Feature: benny-safety

`SOURCE_CHANNEL_ID` and `SOURCE_THREAD_TS` MUST be stored before delegation and MUST NOT be replaced with a reply timestamp or an operations-thread timestamp. The coordinator is the only Slack poster. Child prompts MUST forbid Slack write actions and MUST receive no Slack credentials. Missing parent, deleted parent, or failed preflight MUST produce no post and no tracker issue. Pull requests from this pack MUST be draft-only.

#### Scenario: worker isolation

- **GIVEN** a delegated analysis or media worker
- **WHEN** that worker is spawned
- **THEN** child prompts forbid Slack writes and Slack tokens
- **AND** only the coordinator may post
- **AND** this isolation is prompt-enforced on grok (`MAX_SUBAGENT_DEPTH` is 1, parent fans out)
- **AND** the copied `PreToolUse` hook does not strip Slack MCP tools

#### Scenario: no source root post

- **GIVEN** any Benny run
- **WHEN** it writes to Slack
- **THEN** operational `SKILL.md` and workflow prompts require the frozen `thread_ts`
- **AND** a missing `thread_ts` MUST produce no post
- **AND** that rule is prompt-enforced
- **AND** `automations/benny/grok/bin/fail-closed.sh` does not deny Slack MCP posts
