## ADDED Requirements

### Requirement: Source coordinates stay immutable and workers cannot post

Feature: benny-safety

`SOURCE_CHANNEL_ID` and `SOURCE_THREAD_TS` MUST be stored before delegation and MUST NOT be replaced with a reply timestamp or an operations-thread timestamp. The coordinator is the only Slack poster. Child prompts MUST forbid Slack write actions and MUST receive no Slack credentials. Missing parent, deleted parent, or failed preflight MUST produce no post and no tracker issue. Pull requests from this pack MUST be draft-only.

#### Scenario: worker isolation

- **GIVEN** a delegated analysis or media worker
- **WHEN** that worker is spawned
- **THEN** it has no Slack write tool and no Slack token
- **AND** only the coordinator may post

#### Scenario: no source root post

- **GIVEN** any Benny run
- **WHEN** it writes to Slack
- **THEN** every source-channel post includes the frozen `thread_ts`
- **AND** a missing `thread_ts` produces no post
