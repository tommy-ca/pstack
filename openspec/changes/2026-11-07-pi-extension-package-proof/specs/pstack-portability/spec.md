# pstack-portability — Pi package resource and verification evidence follow-on

## MODIFIED Requirements

### Requirement: Portable package projection preserves roles and lifecycle boundaries
A portable plugin descriptor MUST remain the single package-source authority. Each host projection MUST produce actual host-recognized skill and role artifacts required by the pinned playbooks, and prove discovery by host-native source attribution rather than file existence or generic `plugin list`. Package operations MUST preserve unmanaged user/project files and host settings; when plugin link/install operations target user-scoped roots, native tests MUST first prove the effective root is disposable.

For standalone Pi, the PStack package SHOULD be a thin, opt-in Pi-native **skills resource projection** (no bundled executable extensions); the existing project-local `.pi/settings.json` and reference `pi-essential-extensions.json` MUST NOT be treated as an installed package. Pi package `pi.skills` resource discovery MUST be checked separately from external `pi-subagents` role directory discovery. Package absence, duplicate legacy `@zenspc/pi-pstack` skills or unresolved agent definitions remain PACKAGE GAP, never runtime proof or justification for a new generic PStack dispatcher.

#### Scenario: OMP install omits agents
- **GIVEN** OMP package projection includes skills and a generated pseudo-manifest but no installed `agents/*.md`
- **WHEN** an Arena cross-judge role is dispatched after install
- **THEN** package parity remains unverified until a native role agent actually resolves with the expected model role
- **AND** an installer smoke check cannot substitute for role execution evidence

#### Scenario: Pi skills installed without role definitions
- **GIVEN** Pi loads PStack's `poteto-mode` skill through an opt-in `pi.skills` package
- **WHEN** a PStack named subagent role is requested in a separate consumer project
- **THEN** the package plane MUST remain GAP/BLOCKED unless `pi-subagents` actually resolves the corresponding `agents/*.md` definition
- **AND** `pi.skills` presence alone MUST NOT claim role or runtime parity

#### Scenario: Unreviewed extension package auto-install
- **GIVEN** a PStack Pi package would auto-include third-party Pi extension code or a transitional competing PStack package
- **WHEN** a packaging review runs
- **THEN** it MUST reject the bundled extension or require an explicit, separately reviewed user opt-in
- **AND** no untrusted package activation may be claimed as PStack security enforcement

### Requirement: Verification evidence shapes remain separate and existing
The port MUST reuse `binding.schema.json` for capability classification, `evidence.schema.json` for evidence ledger entries, and `receipt.schema.json` for the four-plane verification receipt without inventing new incompatible enums. The receipt scenario `evidence_level` MUST be `static | offline | observed_live | legacy`. The evidence-ledger `kind` field MUST retain its own `static | runtime | external` semantics; its verdict enum is narrower than the receipt verdict enum. A proposed cross-schema mapping MUST be explicit and schema-validated rather than silently collapsing unlike types. Source-documented/static/offline work MUST NOT prove an `observed_live` runtime claim. Revision freshness and evidence strength MUST be evaluated separately from nominal PASS/FAIL verdict.

Specifically for standalone Pi, a version/package listing and a `pi -p --no-session --no-tools` preflight MUST NEVER alone cause `agent.spawn`, `agent.join`, authorization or sandbox runtime PASS. The existing Pi verifier MUST remain BLOCKED until effect-bound native child and OS policy receipts exist. A cleanup command MUST NOT claim PASS for untracked actors, artifacts or worktrees. The 53 bounded invalid input mutations MUST be called source-contract verification, not native formal model checking.

#### Scenario: existing ledger and receipt distinguish untested execution
- **GIVEN** no OMP model-backed worker could run but offline profile checks passed
- **WHEN** evidence is serialized to the existing ledger and receipt schemas
- **THEN** each artifact validates independently, with any unsupported `UNTESTED` state recorded only in a schema that permits it
- **AND** the runtime plane cannot be promoted to verified or supported on the strength of static/offline evidence

#### Scenario: Pi preflight succeeds but child never launches
- **GIVEN** a Pi executable, matching package versions and `--no-tools` echo return 0
- **WHEN** `scripts/prove_pi_vertical_slice.py` reduces its four-plane receipt
- **THEN** the runtime plane and overall verdict MUST remain BLOCKED
- **AND** there MUST NOT be an `observed_live` child/sandbox scenario until actual child authorization and effects are recorded

#### Scenario: cleanup has no actual actor tracking
- **GIVEN** the Pi preflight has no known child ID, worktree or sandbox-effect ledger
- **WHEN** its cleanup wrapper runs
- **THEN** it MUST return BLOCKED/NOT_VERIFIED rather than PASS
- **AND** a lack of detected side effects MUST NOT be described as proof of cleanup

## ADDED Requirements

### Requirement: Pi extension ownership and source-pinned upgrades stay explicit
Standalone Pi MUST remain a separate namespaced candidate from OMP, with one selected delegated-agent engine, one OS sandbox owner, one tool-call adjudicator and one structured human.ask owner. The minimal coding candidate uses pi-subagents 0.86.0, pi-better-sandbox 0.14.1, pi-verdict 0.16.0, pi-ask-user 0.17.2; pi-web-access 0.47.0 is optional research. An observed newer pi-subagents release 0.87.0 MUST be a distinct, independently verified upgrade candidate rather than automatically changing the active pin. Pi's built-in MCP, tools and sessions MUST not be repackaged as new PStack extensions.

#### Scenario: provider-qualified model would fall back
- **GIVEN** a future upgrade probe names `provider/id` and the chosen provider is not authorized
- **WHEN** Pi-subagents attempts launch
- **THEN** it MUST refuse that provider-specific request rather than silently use a same-named model from another provider
- **AND** a source release note alone MUST NOT count as observed model-family diversity

#### Scenario: drain-aware stop and multi-session lifecycle
- **GIVEN** an upgraded Pi-subagents workflow has active and queued children
- **WHEN** `stop` with `drain:true` is exercised
- **THEN** new child dispatch MUST stop, running children MAY settle and preserve their results
- **AND** no cancelled/stopped workflow or another session's child MAY be counted as an accepted independent reviewer without terminal evidence

### Requirement: Pi authorization and formal verification must not overclaim their enforcement
An enabled pi-verdict tool_call hook MAY reject known unsafe calls, but classifier `allow`/interactive `ask_user` are NOT sufficient to prove mandatory human.gate or OS sandbox enforcement. Any missing/disabled hook, child delegation bypass, custom/MCP trusted-extension effect or unavailable operator MUST remain BLOCKED for privileged actions. The existing functional and formal verification skills MUST expose source-versus-native proof tiers, exact source/pin revisions, negative tests and checker/tool availability; no generic parallel proof service may be introduced.

#### Scenario: classifier allow but hard action lacks authorization
- **GIVEN** an attempted privileged child/custom tool action returns `allow` from pi-verdict but no independently enforced human permission
- **WHEN** the runtime verifier observes effect authorization
- **THEN** it MUST reject a hard-gate PASS claim
- **AND** this PStack Pi candidate MUST retain `human.gate` as GAP

#### Scenario: source mutant tests pass but native checker never runs
- **GIVEN** all 53 finite invalid contract variants are rejected
- **WHEN** `verify-pi-pstack-formal` is evaluated without a real code-linked model checker or native transition proof
- **THEN** it MAY report bounded source-contract PASS only
- **AND** native formal/security proof MUST remain NOT_RUN/BLOCKED

### Requirement: PStack Pi package reuse does not invert upstream or downstream authority
Canonical PStack skills MUST preserve the applied Cursor intent and remain independently usable without Pi or QStack. Pi is an optional host projection; QStack `qstack-mode` may consume independently installed `poteto-mode`, but PStack MUST NOT import QStack, invent a new execution engine or add a model/provider registry to accommodate the Pi package.

#### Scenario: PStack skills loaded in a Pi-free or QStack-free environment
- **GIVEN** a host installs canonical PStack with neither Pi extensions nor QStack
- **WHEN** a normal PStack skill or playbook is invoked on its supported host
- **THEN** upstream PStack semantic behavior and role contracts MUST remain available
- **AND** no Pi-specific package module, quant overlay or additional controller is required
