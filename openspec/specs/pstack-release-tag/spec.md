## Purpose
pstack releases are git tags from `plugin.json` via `grok plugin tag`. GitHub Release is created from the tag.

## Requirements

### Requirement: pstack tags from plugin.json via grok plugin tag

Feature: pstack-release-tag
Rule: one plugin, one git tag namespace
Rule: GitHub Release converges from local or Actions

`scripts/release.sh` MUST run `grok plugin validate` and `grok plugin tag --push`. It MUST NOT pass `--force`. After the tag exists on origin it MUST converge to a GitHub Release with `gh release view` or `gh release create --verify-tag`. Nested grok MUST NOT be the tagger. `.github/workflows/release.yml` MUST run on tags matching `v*` and MUST converge to a GitHub Release the same way. That workflow MUST NOT invoke `grok plugin tag`. It MUST NOT declare `workflow_dispatch`. `docs/guide/13-grok-natives.md` MUST name `grok plugin tag` as the local tag command and MUST name host-shell `grok --sandbox off` for tagging.

#### Scenario: local script tags from the manifest

- **GIVEN** a clean tree on main
- **WHEN** an operator runs `scripts/release.sh` from a host shell
- **THEN** the script calls `grok plugin tag --push`
- **AND** it does not pass `--force`

#### Scenario: GitHub Release follows the tag

- **GIVEN** a pushed tag `v*`
- **WHEN** `.github/workflows/release.yml` runs
- **THEN** it creates a GitHub Release for that tag if one is missing
- **AND** it does not call `grok plugin tag`

#### Scenario: local script converges when Actions is silent

- **GIVEN** origin already has tag `v{plugin.json version}`
- **AND** GitHub has no Release for that tag
- **WHEN** an operator runs `scripts/release.sh` from a host shell
- **THEN** the script does not pass `--force`
- **AND** it creates the GitHub Release with `gh release create --verify-tag`

#### Scenario: both writers no-op when the Release exists

- **GIVEN** origin has the tag
- **AND** GitHub already has a Release for that tag
- **WHEN** `scripts/release.sh` or `release.yml` runs
- **THEN** neither moves the tag
- **AND** neither fails because the Release already exists

#### Scenario: nested grok cannot tag

- **GIVEN** `__GROK_INSIDE_BWRAP` is set
- **WHEN** an operator runs `scripts/release.sh`
- **THEN** the script exits non-zero before `grok plugin tag`
- **AND** the error names host-shell `grok --sandbox off`
