# pstack-setup-overlays — consolidate setup while preserving native safety

## MODIFIED Requirements

### Requirement: Host-neutral entry dispatches to the declared setup skill
Feature: pstack-setup-overlays

`/setup-pstack` MUST remain the sole user-facing setup entry, preserving applied upstream Cursor setup semantics without defining a new orchestration or model-provider runtime. It MUST resolve an active host against the exactly matched typed host profile and dispatch by the profile's declared `setup.source`. For `host-cli`, it MUST read a **host-local setup reference** at `skills/setup-pstack/references/<matched-profile-filename-stem>.md`, after confined regular-file validation, and MUST NOT invoke a second public setup skill. After migration, `SetupProjection` MUST have no `skill` or `reference` pointer; the reference is derived from the validated profile filename. The shared skill MUST NOT inline any host home path, CLI, model slug or effort enum. No missing/invalid/candidate host may borrow a different host's setup.

#### Scenario: no setup block is a reported gap
- **GIVEN** a host profile with no `setup` key
- **WHEN** `/setup-pstack` resolves that host
- **THEN** it reports a GAP naming the host and missing declaration
- **AND** it runs no host-specific setup steps and writes no other host's files

#### Scenario: host-cli setup is read only from the matching trusted reference
- **GIVEN** a supported Grok profile file `grok.json` with `source: host-cli`
- **WHEN** `/setup-pstack` resolves the active host and exact profile `host` field
- **THEN** it reads only `skills/setup-pstack/references/grok.md` after path validation
- **AND** it MUST NOT launch `setup-pstack-grok` as another user-facing skill

### Requirement: Optional setup writes grok overlays
Feature: pstack-setup-overlays

Official Cursor `/setup-pstack` writes `~/.cursor/rules/pstack-models.mdc`; that path and Cursor model variants are NOT native Grok setup. This port's Grok-only setup reference MUST preserve the current Grok Build file shapes: `~/.grok/pstack-models.toml` with top-level role keys (not a `[models]` table) and separate `[effort]`, and scoped `~/.grok/roles/pstack:<role-key>.toml` containing only `description` and `reasoning_effort`. Missing override uses the shipped Grok default and agent-frontmatter effort; any real chosen slug or effort token requires host-specific validation before write. It MUST NOT read or write Cursor mdc paths. A static projection or config write MUST NOT be mistaken for verified native model acceptance.

#### Scenario: overlay stem matches spawn type
- **GIVEN** the Grok-only setup reference accepted valid detected effort choices for `feature`
- **WHEN** it writes the managed role overlay
- **THEN** the path is `~/.grok/roles/pstack:feature.toml`
- **AND** model TOML keys stay bare (`feature`, not `pstack:feature`)
- **AND** neither a `[models]` table nor a Cursor mdc file is written

#### Scenario: model inheritance differs from Grok effort fallback
- **GIVEN** the Grok role agent has shipped frontmatter `effort`
- **WHEN** a role's model and effort both select `inherit-parent` or `auto`
- **THEN** the model override is omitted and the pstack-managed effort role file is removed
- **AND** the effective effort MUST be described as agent-frontmatter fallback unless the actual host proves otherwise

## ADDED Requirements

### Requirement: Setup reference paths are derived, confined, and host-bound
Feature: pstack-setup-overlays

The host-local setup reference path MUST be derived exclusively from the basename of the exact validated profile file found for the active `host` ID. It MUST resolve under `skills/setup-pstack/references/`, reject symlinks/path traversal/absolute paths/nonfiles, and fail closed if missing. No configuration field, path supplied by a user, or filename stem masquerading as a host ID may select a different host's instructions.

#### Scenario: a host ID is not a filename
- **GIVEN** a profile file `copilot.json` declaring `host: github:copilot`
- **WHEN** the active host is resolved
- **THEN** lookup MUST compare the exact declared `host` ID before deriving any reference
- **AND** the bare `copilot` string MUST NOT be accepted as a valid equivalent host ID

#### Scenario: reference is missing or escapes the trusted directory
- **GIVEN** a supported host-cli profile whose convention-derived reference is missing, symlinked or not a regular file
- **WHEN** setup attempts to load native instructions
- **THEN** it reports GAP/BLOCKED without invoking a different host's reference
- **AND** it performs no probe and no configuration write

### Requirement: Setup source modes have one typed, closed schema
Feature: pstack-setup-overlays

`schemas/portability/setup-projection.schema.json` and `scripts/portability_types.py::SetupProjection` MUST express the same discriminated source/effort/catalog/overlay matrix, without a legacy `skill` pointer or replacement `reference` pointer after the coordinated migration. `host-cli` requires `effort: live-enum` and a host-home catalog, `host-catalog` requires `effort: none` and an existing projected repo catalog, `inherit` requires `effort: inherit-parent` and no paths, and `none` requires `effort: none` and no paths. Candidate hosts MUST NOT claim active `host-cli` support. Invalid/unknown keys and source-field combinations MUST be rejected at the typed boundary.

#### Scenario: invalid source or leftover dispatch field
- **GIVEN** a setup JSON object containing `skill`, `reference`, an unsupported source or an invalid effort/field combination
- **WHEN** profile-schema validation runs after migration
- **THEN** it fails before any reference lookup, model discovery or write
- **AND** the other host's defaults MUST NOT be used as a fallback

#### Scenario: unsupported host cannot probe native CLI
- **GIVEN** a candidate host profile configured with `source: host-cli`
- **WHEN** setup projection validation runs
- **THEN** it is rejected as unproven
- **AND** neither native CLI discovery nor configuration writes run

### Requirement: Role and budget choices reuse existing authorities
Feature: pstack-setup-overlays

Canonical `pstack.package.json#roles` MUST remain the sole role taxonomy (including scalar versus array-valued panel roles), and `scripts/model_role_resolver.py` MUST remain the sole override-precedence implementation. Setup MUST retain applied upstream steps for discovery, current-state load, model budget/per-role choice where the active host supports it, validation, confirmation, and optional verification. Cursor-specific budget/model examples MUST NOT become the Grok live enum; detected available slugs/tokens are the only real values offered. `inherit-parent`/`auto` MUST not fabricate a model identity, successful spawn, independent panel or effort-inheritance claim.

#### Scenario: invalid or unavailable chosen model
- **GIVEN** a role choice names an unconfirmed model or an effort token absent from the host's usable enum
- **WHEN** setup validates it
- **THEN** it requests a valid choice or reports BLOCKED
- **AND** it persists no substituted or unverified model/effort value

#### Scenario: panel list is not independent evidence
- **GIVEN** a panel role configured as a list with repeated model-family entries
- **WHEN** setup reports the mapping
- **THEN** the panel retains requested seat cardinality
- **AND** configuration of seats MUST NOT be described as completed or independent reviewers

### Requirement: Both optional verification creation paths remain available
Feature: pstack-setup-overlays

The unified setup workflow MUST preserve the upstream distinct optional post-setup offers to `create-verification-skill` (behavioral/app verification) and `create-formal-verification-skill` (model checking/proof for a concrete high-impact target). Each MUST be offered only if missing, requested/accepted before invocation, and routed through the existing skill rather than a duplicate generator. The Grok-specific restriction on config writes applies to the setup phase; generation of a separate project-local skill requires a separate authorized follow-up action.

#### Scenario: project already has a formal verifier
- **GIVEN** the project contains a relevant formal verification skill, but no applicable behavioral verification skill
- **WHEN** model setup completes
- **THEN** it MAY offer only the missing behavioral verification skill
- **AND** it MUST NOT regenerate or replace the existing formal verifier unasked

#### Scenario: operator declines optional verification
- **GIVEN** setup completes and the operator declines both optional offers
- **WHEN** confirmation is emitted
- **THEN** no app verification skill or formal-verification output is created
- **AND** only the explicitly chosen host-native setup files may have changed

### Requirement: Packaged profiles are the only editable host authority
Feature: pstack-setup-overlays

The nine existing machine-readable host profiles MUST remain under `skills/setup-pstack/profiles/` and be the only editable source. The root `profiles/` tree MAY remain as a deterministic, byte-identical generated compatibility output while current project and plugin consumers require it. `resolve_profiles_dir` MUST prefer canonical packaged data; if both copies exist, a mismatch MUST fail profile validation or packaging rather than silently preferring a stale root copy. Profiles MUST NOT be moved to `poteto-mode/references` or used to assert capabilities lacking real host evidence.

#### Scenario: root profile diverges from the packaged profile
- **GIVEN** both trees exist and one root profile is stale
- **WHEN** profile resolution, validation or packaging runs
- **THEN** the parity gate fails deterministically
- **AND** no stale root content is allowed to choose a setup target

#### Scenario: installed plugin only includes packaged source
- **GIVEN** an installed plugin includes `skills/setup-pstack/profiles` but no root compatibility mirror
- **WHEN** `/setup-pstack` resolves the host
- **THEN** it loads the packaged profile without requiring root files
- **AND** it does not invent unsupported host capabilities

### Requirement: Native setup writes are scoped, idempotent and evidence-graded
Feature: pstack-setup-overlays

Setup MUST preserve user-owned configuration outside explicitly managed host paths, make repeated identical setup choices converge without unintended mutation, and report only actually written/projected paths. `host-catalog`, `inherit`, `none` and absent setup MUST perform no runtime setup writes. A planning/config validation may report PLANNED/DEGRADED/BLOCKED, but never VERIFIED solely because a file exists or was written. Missing host, checker or actual independent review must remain NOT_RUN/BLOCKED.

#### Scenario: repeat Grok setup with unrelated user files
- **GIVEN** existing valid managed Grok overlays and an unrelated user-owned native role file
- **WHEN** setup runs twice with identical validated choices
- **THEN** the final pstack-managed content is byte-equivalent and unrelated files remain unchanged
- **AND** no native execution success is claimed without direct observation

#### Scenario: host-catalog is a project-time projection
- **GIVEN** a Codex profile with `source: host-catalog`
- **WHEN** `/setup-pstack` reports setup status
- **THEN** it names the existing projected catalog and its provenance
- **AND** it does not write `~/.grok` or claim the catalog was modified at runtime

### Requirement: Retire legacy setup only after all callers and package surfaces migrate
Feature: pstack-setup-overlays

The implementation MUST migrate native setup references, role and effort links, both `grok.json` copies, the existing typed schema/parser, verifiers, package manifests/projections, boundary scanner, docs and tests before deleting `skills/setup-pstack-grok/` and `SetupProjection.skill` together. Historical audit documents MAY retain those names but MUST NOT advertise them as live. The refactor MUST NOT introduce a permanent second dispatcher, model registry, adapter SDK or QStack reverse dependency.

#### Scenario: one caller still depends on the removed skill
- **GIVEN** a shipped/current test, manifest, resolver, schema or skill link still requires `setup-pstack-grok`
- **WHEN** the old skill is removed
- **THEN** the package or static caller gate MUST fail
- **AND** the migration MUST NOT be marked complete

#### Scenario: old spec still requires dispatch to a separate setup skill
- **GIVEN** the living `pstack-setup-overlays` requirement still describes `setup.skill` dispatch
- **WHEN** the new setup reference behavior is applied
- **THEN** the change MUST modify that original requirement, not only add a competing one
- **AND** stale spec/implementation parity MUST be reported as a failed gate
