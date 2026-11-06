# pstack-setup-overlays: single-entry host references and packaged profile authority

## ADDED Requirements

### Requirement: One public setup skill preserves upstream setup semantics
The port MUST expose `skills/setup-pstack/SKILL.md` as the sole user-facing model/effort setup skill. It MUST preserve canonical Cursor PStack intent (discover available models, load current choices, budget/per-role/panel selection, validate, host-owned persistence, confirm, optional verification). It MUST NOT require a second setup skill for one host or inline any host-specific shell commands, model slugs, effort enums or home paths.

#### Scenario: A Grok-specific setup step is requested
- **GIVEN** a supported installed Grok host and a valid Grok setup projection
- **WHEN** the operator invokes `/setup-pstack`
- **THEN** the entry MUST read only that host's validated setup reference
- **AND** it MUST not route through a separate public `/setup-pstack-grok` skill

### Requirement: Host-specific setup instructions are safely selected references
The existing typed `SetupProjection` MAY temporarily accept one validated `reference` in place of its legacy `skill` on a `host-cli` projection. Relative references MUST be confined to `skills/setup-pstack/references/`; non-CLI hosts MUST NOT declare setup execution references. Invalid, missing, outside-tree or ambiguous references MUST fail closed with no other-host fallback.

#### Scenario: Reference points outside setup references
- **GIVEN** a profile that declares `reference: "../../other-host.md"` or an absolute/symlink escape path
- **WHEN** setup resolves its instructions
- **THEN** validation MUST reject the reference
- **AND** no native probe or config write MAY run

#### Scenario: Legacy and new dispatch are both declared
- **GIVEN** `source: host-cli` with both `skill` and `reference`
- **WHEN** projection validation runs
- **THEN** it MUST refuse ambiguous dispatch
- **AND** it MUST NOT silently prefer one route

### Requirement: Only active-host capabilities authorize setup actions
Setup MUST bind the active session to the exact declared host ID and profile support state. It MUST NOT infer native capabilities from package presence, repo paths, default model examples, or other hosts' catalogs. `host-catalog`, `inherit`, `none` and candidates with no authorized CLI probe MUST keep their current honest no-write and GAP/BLOCKED behavior.

#### Scenario: Non-Grok host reaches Grok write instruction
- **GIVEN** Codex or an unverified candidate host is active
- **WHEN** setup is invoked
- **THEN** Grok CLI or `~/.grok/` writes MUST NOT be selected
- **AND** unsupported setup MUST be reported as no-write, GAP, or BLOCKED

### Requirement: Role and budget decisions have one authority
`pstack.package.json#roles` MUST remain the sole role taxonomy, and `scripts/model_role_resolver.py` MUST remain the sole precedence planner. Setup MUST preserve scalar and panel cardinality, handle `inherit-parent`/`auto` without fabricating model identities, and offer only host-supported model/effort selections. Cursor's budget tokens MUST be translated only when observed supported; unlisted Grok effort tokens MUST NOT be offered.

#### Scenario: A model slug or effort token is unavailable
- **GIVEN** an offered model or effort value that the active host has not established as valid
- **WHEN** setup validates before writing
- **THEN** it MUST refuse or request a supported choice
- **AND** it MUST NOT persist the unverified value or substitute another host's default

#### Scenario: Grok effort alias does not guarantee parent effort
- **GIVEN** a Grok plugin agent with shipped frontmatter `effort` and an `[effort]` override set to `inherit-parent` or `auto`
- **WHEN** setup removes the corresponding managed role overlay
- **THEN** confirmation MUST describe the effective fallback as plugin-agent frontmatter unless native evidence proves parent effort inheritance
- **AND** it MUST NOT claim that omitting the overlay causes direct parent-session effort inheritance

### Requirement: Packaged profiles are a single canonical machine-readable source
`skills/setup-pstack/profiles/` MUST hold the editable canonical host declarations for skill distribution. During migration `profiles/` MAY remain a deterministic generated compatibility mirror, never an independently maintained source. All host discovery and consumers MUST use a validated resolver and reject diverged copies; a mirror MUST NOT silently override the canonical packaged data.

#### Scenario: Repository mirror drifts
- **GIVEN** a root profile differs from its packaged counterpart
- **WHEN** profile validation or packaging runs
- **THEN** the divergence MUST fail the parity gate
- **AND** no stale root profile MAY silently determine the setup target

### Requirement: Native writes are idempotent, ownership-scoped and honestly reported
Setup MUST preserve user-owned configuration outside its documented managed paths; repeats MUST be idempotent. A successful static/profile validation or config write MUST NOT be described as a verified native model execution. Missing checker, unavailable host, or non-run panel MUST stay explicitly BLOCKED/NOT_RUN.

#### Scenario: Re-run with unchanged Grok setup choices
- **GIVEN** valid existing pstack-managed overlays and unrelated user-owned files
- **WHEN** setup is run with identical choices
- **THEN** pstack-managed files MUST remain equivalent and no unrelated files MAY be overwritten
- **AND** confirmation MUST distinguish completed writes from live model acceptance

### Requirement: Retired skill removal is gated by caller and package migration
`skills/setup-pstack-grok/` MUST NOT be removed before all live profile references, skill links, plugin packaging and verification tests are migrated. Historical docs MAY retain its name as prior evidence but MUST NOT advertise it as invocable.

#### Scenario: Unmigrated consumer references the deleted skill
- **GIVEN** an executable or shipped skill still points at `setup-pstack-grok`
- **WHEN** the old skill is removed
- **THEN** the migration gate MUST fail
- **AND** the change MUST NOT claim complete host-neutral setup
