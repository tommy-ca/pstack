## MODIFIED Requirements

### Requirement: pstack tags from plugin.json via grok plugin tag

Feature: pstack-release-tag
Rule: one plugin, one git tag namespace
Rule: GitHub Release converges from local or Actions
Rule: tag name is `v` plus `plugin.json` version at HEAD

`scripts/release.sh` MUST run `grok plugin validate` and `grok --sandbox off plugin tag --push`. It MUST NOT pass `--force`. If the local tag exists and origin does not, it MUST `git push origin` that ref. After the tag exists on origin it MUST converge to a GitHub Release with `gh release view` or `gh release create --verify-tag`. Nested grok MUST NOT be the tagger. `.github/workflows/release.yml` MUST run on tags matching `v*` and MUST converge to a GitHub Release the same way. That workflow MUST NOT invoke `grok plugin tag`. It MUST NOT declare `workflow_dispatch`. A successful workflow run on that tag is the dispatcher proof. GitHub Release author is first writer. `docs/guide/13-grok-natives.md` MUST name `grok --sandbox off plugin tag --push` as the local tag command.

#### Scenario: local script tags from the manifest

- **GIVEN** a clean tree on main
- **WHEN** an operator runs `scripts/release.sh` from a host shell
- **THEN** the script calls `grok --sandbox off plugin tag --push`
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

#### Scenario: local tag exists and origin does not

- **GIVEN** `refs/tags/v{plugin.json version}` exists locally
- **AND** origin does not have that tag
- **WHEN** `grok --sandbox off plugin tag --push` fails
- **THEN** the script runs `git push origin` for that tag
- **AND** it does not pass `--force`

#### Scenario: Actions run proves the dispatcher

- **GIVEN** origin has a `v*` tag
- **AND** `release.yml` already existed on the default branch before that tag was pushed
- **WHEN** the workflow finishes
- **THEN** a GitHub Actions run for that tag exists with event `push`
- **AND** a GitHub Release for that tag exists
- **AND** the Release author is not required to be `github-actions`
