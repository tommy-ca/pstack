## ADDED Requirements

### Requirement: Version is SemVer with grokbuild adapter identity

Feature: pstack-release-tag
Rule: TagName is v plus plugin.json version
Rule: identity is adapter lineage, not ship day

`plugin.json` version MUST match `MAJOR.MINOR.PATCH-grokbuild.N` (SemVer 2.0 prerelease). MAJOR.MINOR.PATCH tracks Cursor pstack when that is the overlay base. N is the grok-build adapter counter. The version MUST NOT be calendar-only (`YYYY.MM.DD`, `YYYY.MM.MICRO`) and MUST NOT use a date as the uniqueness key. Ship day belongs in GitHub Release notes (`--generate-notes`). Existing tags MUST NOT be moved.

#### Scenario: live version encodes adapter lineage

- **GIVEN** `plugin.json`
- **WHEN** version is read
- **THEN** it matches `MAJOR.MINOR.PATCH-grokbuild.N`
- **AND** it does not match a date-only CalVer string

#### Scenario: date is not the tag identity

- **GIVEN** a pstack release
- **WHEN** the operator reads the version
- **THEN** the string names grokbuild adapter identity
- **AND** the ship day is on the GitHub Release, not required in the version
