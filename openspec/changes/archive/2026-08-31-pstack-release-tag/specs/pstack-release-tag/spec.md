## ADDED Requirements

### Requirement: pstack tags from plugin.json via grok plugin tag

Feature: pstack-release-tag
Rule: one plugin, one git tag namespace

`scripts/release.sh` MUST run `grok plugin validate` and `grok plugin tag --push`. It MUST NOT pass `--force`. `.github/workflows/release.yml` MUST run on tags matching `v*` and MUST create a GitHub Release with `gh release create`. That workflow MUST NOT invoke `grok plugin tag`. `docs/guide/13-grok-natives.md` MUST name `grok plugin tag` as the local release command.

#### Scenario: local script tags from the manifest

- **GIVEN** a clean tree on main
- **WHEN** an operator runs `scripts/release.sh`
- **THEN** the script calls `grok plugin tag --push`
- **AND** it does not pass `--force`

#### Scenario: GitHub Release follows the tag

- **GIVEN** a pushed tag `v*`
- **WHEN** `.github/workflows/release.yml` runs
- **THEN** it creates a GitHub Release for that tag
- **AND** it does not call `grok plugin tag`

## MODIFIED Requirements

None.

## REMOVED Requirements

None.

## RENAMED Requirements

None.
