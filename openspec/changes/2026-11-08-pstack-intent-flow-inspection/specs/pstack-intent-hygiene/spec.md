# pstack-intent-hygiene — inspect and validate the intent-driven workflow

## ADDED Requirements

### Requirement: Active intent-driven artifact chains have a host-neutral read-only inspector

The existing OpenSpec change helper MUST expose a deterministic `proposal -> specs -> design -> adr -> tasks` stage inspection for active changes, independent of the OpenSpec executable and independent of the active harness. It MUST report the schema declaration, per-stage artifact presence, missing artifacts, and task checkbox state without asserting OpenSpec validity or completion of implementation. It MUST ignore archived change directories and reject path traversal or symlink files presented as legitimate artifacts.

#### Scenario: Complete planning artifact chain with pending implementation

- **GIVEN** an active intent-driven change contains its metadata and all five required artifacts
- **AND** `tasks.md` still has unchecked tasks
- **WHEN** the operator runs `openspec_change.py --status --json`
- **THEN** the response marks the planning artifact chain present and implementation tasks in progress
- **AND** it explicitly describes its evidence as filesystem-only, not OpenSpec or host runtime proof

#### Scenario: Partial change reports the exact missing stage

- **GIVEN** an active change is missing its `adr.md`
- **WHEN** the inspector evaluates the change
- **THEN** it reports `adr` as missing and as the next missing stage
- **AND** it does not alter or archive any files

#### Scenario: Historical archive is not inspected as an active change

- **GIVEN** the repository has active and archived OpenSpec changes
- **WHEN** the operator requests the active status report
- **THEN** only direct active directories appear in stable name order
- **AND** the archive tree remains untouched

#### Scenario: Symlinked artifacts and invalid names cannot conceal gaps

- **GIVEN** an invalid `../` change name or an artifact symlink pointing to another file
- **WHEN** the inspector reads change state
- **THEN** it rejects unsafe change names and does not count symlinked artifacts as present
- **AND** no host-specific tools or directory writes are required

### Requirement: Strict intent-driven validation must fail closed separately from inspection

PStack MUST provide a distinct strict verification command that checks whether a selected active change (or all active changes) has an intent-driven artifact chain, then uses the real OpenSpec CLI to validate the `intent-driven` schema and the actual change specification. Missing CLI, missing artifacts, malformed schema, or strict validation failure MUST NOT be reported as PASS. It MUST preserve explicit `--change` targeting when several active changes coexist.

#### Scenario: OpenSpec CLI is absent

- **GIVEN** an artifact-complete active change and an environment without OpenSpec CLI
- **WHEN** strict verification is requested
- **THEN** it reports BLOCKED with a nonzero exit
- **AND** no prior filesystem-only status becomes strict validation PASS

#### Scenario: Strict schema and change checks are ordered

- **GIVEN** two complete active changes
- **WHEN** the operator runs strict verification for all
- **THEN** OpenSpec schema validation runs before strict validation of each change
- **AND** a failing command fails verification without bypassing the error

#### Scenario: Explicit change scope in an evolving multi-change repository

- **GIVEN** multiple active changes including one incomplete draft
- **WHEN** the operator verifies one complete change using `--change`
- **THEN** verification targets the selected change rather than claiming all drafts passed
- **AND** the incomplete draft remains visible in the separate status report

### Requirement: OpenSpec intent-driven setup must preserve existing host and archive contracts

The repository MUST retain the already-vendored intent-driven schema and its immutable accepted ADR rules, retain six shipped harness adapters, and avoid importing OpenCode-only agent runtimes or duplicate configuration as mandatory PStack dependencies. `skip_specs: true` remains an explicit docs-only exception and does not exempt other artifacts. Source-only validation MUST remain distinct from accepted source/spec, native harness verification and independent reviews.

#### Scenario: Docs-only skip specs is scoped

- **GIVEN** a docs-only change declaring `skip_specs: true`
- **WHEN** the artifact inspector evaluates its otherwise complete intent chain
- **THEN** the specifications stage is marked exempt rather than fabricating a spec file
- **AND** proposal, design, ADR, task list and metadata still must be present

#### Scenario: Existing harnesses remain independent

- **GIVEN** a PStack harness without OpenCode or an installed OpenSpec CLI
- **WHEN** it uses ordinary canonical PStack skills
- **THEN** existing host execution continues without a new agent SDK or template-specific `opencode.json`
- **AND** OpenSpec strict validation remains separately blocked if its CLI is absent
