## ADDED Requirements

### Requirement: Sync script prints pin and recipe without copying

Feature: pstack-sync-from-upstream

`scripts/sync-from-upstream.py --pin` MUST print the 40-hex `tree` SHA from `UPSTREAM`. `--recipe` MUST name `adapt-harness.py`, `verify-harness.py`, skip `make-bot-ui`, and `pstack:<role>`. Default invocation MUST print the recipe. The script MUST NOT overwrite this tree unless a later flag is added.

#### Scenario: pin matches UPSTREAM

- **GIVEN** `UPSTREAM` contains `tree <40-hex>`
- **WHEN** `python3 scripts/sync-from-upstream.py --pin` runs
- **THEN** stdout is that SHA
