## ADDED Requirements

### Requirement: Adapter counter advances when HEAD outruns the last tag

Feature: pstack-release-tag
Rule: never move an existing grokbuild tag
Rule: later adapter work on the same Cursor base increments N

When origin already has `vMAJOR.MINOR.PATCH-grokbuild.N` and `main` has later adapter work, the next release MUST set `plugin.json` to `MAJOR.MINOR.PATCH-grokbuild.(N+1)` and MUST tag that new version. The existing tag MUST stay on its original commit. The six tracked manifest surfaces MUST keep lockstep with the new root version. Nested grok MUST NOT be the tagger.

#### Scenario: bump N instead of moving the last tag

- **GIVEN** origin has tag `vMAJOR.MINOR.PATCH-grokbuild.N`
- **AND** `main` has later adapter commits
- **WHEN** the next pstack release is prepared
- **THEN** root `plugin.json` version is `MAJOR.MINOR.PATCH-grokbuild.(N+1)`
- **AND** tag `vMAJOR.MINOR.PATCH-grokbuild.N` still points at the commit it already had

#### Scenario: lockstep follows the new adapter counter

- **GIVEN** root `plugin.json` is the new `MAJOR.MINOR.PATCH-grokbuild.(N+1)`
- **WHEN** the manifest verification test reads the six tracked version surfaces
- **THEN** every surface equals the new root version

#### Scenario: host-shell script tags the new version

- **GIVEN** a clean tree on `main` at the bump commit
- **WHEN** an operator runs `scripts/release.sh` from a host shell
- **THEN** origin gains tag `v` plus the new root version
- **AND** GitHub has a Release for that tag
- **AND** the script does not pass `--force`
