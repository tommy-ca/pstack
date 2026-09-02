## Purpose
pstack releases are git tags from `plugin.json` via `grok plugin tag`. GitHub Release is created from the tag.

## Requirements

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

### Requirement: Adapter identity is not catalog sibling identity

Feature: pstack-release-tag
Rule: one plugin, Cursor overlay lineage
Rule: do not copy catalog name-in-version

`plugin.json` version MUST remain `MAJOR.MINOR.PATCH-grokbuild.N`. It MUST NOT use catalog sibling grammar `MAJOR.MINOR.PATCH-<plugin-name>.N` and MUST NOT use `-pstack.N`. pstack is one plugin in one git repo. The grokbuild token is adapter lineage, not a package-name namespace. Catalog uniqueness is a different problem (many local plugins, one tag namespace) and MUST NOT be solved here. Existing tags MUST NOT be moved.

#### Scenario: live version is grokbuild, not pstack-name

- **GIVEN** `plugin.json`
- **WHEN** version is read
- **THEN** it matches `MAJOR.MINOR.PATCH-grokbuild.N`
- **AND** it does not end with `-pstack.N`

#### Scenario: catalog grammar is not copied

- **GIVEN** a later change that would unify with grok-build-plugins
- **WHEN** pstack version is considered
- **THEN** the grammar stays `MAJOR.MINOR.PATCH-grokbuild.N`
- **AND** existing tags are not moved

### Requirement: pstack is a single-plugin git repo

Feature: pstack-release-tag
Rule: one plugin, one git tag namespace
Rule: not a catalog sibling folder

pstack MUST remain the `tommy-ca/pstack` repository with `plugin.json` at the repo root. It MUST NOT relocate into `grok-build-plugins/pstack` or `plugins/pstack`. `scripts/release.sh` MUST keep tagging this repo. Catalog tagging MUST NOT become the pstack tagger. Documented install MUST stay `grok plugin install tommy-ca/pstack --trust`. Existing tags MUST NOT be moved.

#### Scenario: plugin.json stays at repo root

- **GIVEN** `plugin.json` at the repository root
- **WHEN** `grok plugin tag` runs from this checkout
- **THEN** the tag is created in `tommy-ca/pstack`
- **AND** the version grammar stays `MAJOR.MINOR.PATCH-grokbuild.N`

#### Scenario: catalog nest is rejected

- **GIVEN** a later change that would copy this tree into grok-build-plugins
- **WHEN** pstack location is considered
- **THEN** the plugin remains this repository
- **AND** existing tags are not moved

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
