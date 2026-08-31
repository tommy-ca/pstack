## ADDED Requirements

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
