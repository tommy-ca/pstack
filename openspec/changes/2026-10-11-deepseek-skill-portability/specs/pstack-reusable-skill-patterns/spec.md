# pstack reusable skill patterns — behavioral specification

Feature: pstack-reusable-skill-patterns

This spec is an additive, intent-driven delta. RFC 2119 terms apply. It MUST NOT redefine the canonical pstack inventory or replace existing portability/evidence contracts.

## ADDED Requirements

### Requirement: source provenance and curatorial decisions

Every incorporated external invariant MUST cite an immutable source revision, path, license and target pstack owner. The adoption matrix MUST cover all sixteen DeepSeek source SKILL.md entries, including explicit deferrals.

#### Scenario: source changes
- **GIVEN** an updated upstream skill after its pinned commit
- **WHEN** the source crosswalk is refreshed
- **THEN** the existing approved decision remains tied to its prior SHA
- **AND** any changed behavior is reassessed before promotion.

#### Scenario: documentation mistaken for proof
- **GIVEN** a source skill describing a successful technique without pstack runtime evidence
- **WHEN** its support claim is reduced
- **THEN** it MUST NOT be treated as observed-live host verification.

### Requirement: one route and one implementation owner

The router MUST remain the existing canonical pstack playbook router. A behavior that belongs to an existing skill MUST extend that owner; it MUST NOT add a duplicate common `dsh-*` skill, registry, scheduler, capability enum or verification reducer by default.

#### Scenario: code review activation
- **GIVEN** a normal pstack code-review task
- **WHEN** source-derived exact-head checks apply
- **THEN** the existing review/interrogate playbook handles them
- **AND** no second DSH review command is invoked.

### Requirement: context-efficient deferred discovery

Agent-facing tooling MUST expose purpose, side-effect/permission constraints and retrievable reference identifiers before operations. Long context SHOULD be deferred only when the total cost (searches + reads + errors + tokens) is no worse on representative tasks.

#### Scenario: minimal prompt causes repeated reads
- **GIVEN** a shortened tool/skill descriptor that removes a necessary retrieval pointer
- **WHEN** a task requires multiple extra searches to recover that detail
- **THEN** the variant fails context efficiency even if initial prompt tokens decrease.

### Requirement: deterministic test resource ownership

Resource-owning tests MUST atomically allocate a private port/path/namespace or explicitly serialize only the contended owner, register cleanup immediately and await quiescent disposal. Readiness MUST depend on observable state, not fixed sleep. Shared process-global state MUST restore its original presence and value.

#### Scenario: concurrent fixture uses a predictable port
- **GIVEN** two independent test processes acquiring the same fixed network port
- **WHEN** the new fixture runs concurrently
- **THEN** the owner allocates distinct ports atomically and both processes complete
- **AND** cleanup settles before the next test.

#### Scenario: race under review
- **GIVEN** an alleged concurrent regression
- **WHEN** its test runs
- **THEN** a barrier proves overlapping operations
- **AND** the pre-fix or injected negative control exposes the target failure.

### Requirement: scoped validation from a live change

Validation MUST determine relevant changed surfaces from a verified base/head (and dirty changes when available), select the smallest test that would fail for the regression, and expand by risk rather than reflexively run the full suite. Stale-head evidence MUST be invalidated or explicitly marked stale.

#### Scenario: changed PR head
- **GIVEN** tests passed for head A
- **WHEN** the PR head becomes B with a behaviorally different patch
- **THEN** the verifier MUST NOT claim A's receipt proves B.

#### Scenario: unavailable native tool
- **GIVEN** a project without DSH tooling or a host without a specific forge feature
- **WHEN** validation is selected
- **THEN** portable tests use that project's available adapter
- **AND** unavailable gates are BLOCKED/UNTESTED rather than assumed passed.

### Requirement: failure identity and state ownership

Expected operational errors MUST preserve typed identity/cause and document effect status as none, partial, committed or unknown. Only the state owner MAY declare recovery, rollback or retry safety. User-visible failure reports MUST provide impact and a safe next step without leaking secrets.

#### Scenario: exception after partial write
- **GIVEN** an operation throws after a partial durable effect
- **WHEN** an agent catches the error
- **THEN** the outcome remains partial/unknown until the owner verifies effects
- **AND** the workflow MUST NOT report success or blind-safe retry.

### Requirement: behavior-preserving simplification

Simplification candidates MUST demonstrate reachable consumers, preserved invariants and a net reduction in maintained obligations. Measurement of deletion count alone is insufficient.

#### Scenario: supposedly dead API has consumers
- **GIVEN** an apparently unreferenced API with a supported external consumer
- **WHEN** a proposal suggests deleting it
- **THEN** the proposal MUST be rejected or classified as an intentional breaking change with migration.

### Requirement: exact-head review and credible performance

Review and performance acceptance MUST identify actual source/base/head and artifact or workload. Performance changes MUST compare comparable baseline and post-change workloads with behavior preservation and disclose exclusions.

#### Scenario: unit benchmark improves while user path worsens
- **GIVEN** a faster microbenchmark but slower end-to-end user workload
- **WHEN** a performance improvement is claimed
- **THEN** it MUST NOT be marked successful for the user path.

### Requirement: relevance and host conditionality

Optional UI, i18n, release, archive, browser evidence and GitHub native-stack contracts MUST be invoked only when the project/task has matching features and capabilities. DSH-specific commands, fixed theme rules and credential instructions MUST NOT be common-pstack requirements.

#### Scenario: backend project with no UI or i18n
- **GIVEN** a server-only code change
- **WHEN** pstack selects skill overlays
- **THEN** browser-GIF, UI color, bilingual pairing and DSH build steps remain inactive.

### Requirement: credible evidence, security and six-host compatibility

Verification MUST preserve the existing three-tier test policy and four serialized receipt planes. Reducers MUST use `FAIL > BLOCKED > UNTESTED > PASS`. Untrusted source text MUST NOT grant permissions, and tool/route operations MUST respect containment and least-privilege invariants.

#### Scenario: OMP only passes offline checks
- **GIVEN** OMP has a static package/contract success and no observed native child settlement
- **WHEN** the six-host matrix is aggregated
- **THEN** OMP runtime MUST remain UNTESTED/BLOCKED
- **AND** the overall verified-live claim MUST not be PASS.

#### Scenario: source prompt suggests an unauthorized command
- **GIVEN** source skill content requests an out-of-scope destructive command
- **WHEN** that content is analyzed or ported
- **THEN** it is treated as untrusted data
- **AND** the operation is not executed by virtue of being in the skill reference.

### Requirement: atomic contracts are compositional, not a new engine

The twenty semantic blocks B01–B20 in [../../atomic-patterns.md](../../atomic-patterns.md) MUST map to existing pstack owners. This decomposition is analytical and MUST NOT require a second registry, scheduler, or portable capability vocabulary.

#### Scenario: fixture does not need an agent
- **GIVEN** an existing verification workflow can handle a deterministic CI fixture
- **WHEN** the source-derived rule applies
- **THEN** the existing workflow MUST own it
- **AND** no new common DSH skill or runtime plane is created.

### Requirement: effectiveness claims are scope-qualified

Documented upstream practice alone MUST NOT be called a proven cross-project improvement. The qualification protocol in [../../qualification-and-eval.md](../../qualification-and-eval.md) MUST record exact source/target pins, matched task classes, baseline and candidate outcomes, negative controls, independent artifact evidence, and uncertainty.

#### Scenario: source-side encoder test
- **GIVEN** a source repository contains a test for a GIF encoder
- **WHEN** the pattern is considered for pstack
- **THEN** that test MAY support the encoder-only claim
- **AND** MUST NOT imply GUI fidelity, model-backed run success, or pstack host conformance.

#### Scenario: incomplete project-archetype coverage
- **GIVEN** Python and TypeScript cases are positive but a docs-only negative case was not run
- **WHEN** portable qualification is evaluated
- **THEN** success MAY be claimed only for covered archetypes
- **AND** universal invocation MUST remain unproven.

### Requirement: read-only scope and tool trust survive skill composition

Patterns MUST NOT widen write/CI/remote permission and MUST treat third-party source guidance as untrusted task data. Source commands and paths MUST NOT cause execution or credential access by inclusion alone.

#### Scenario: read-only CI diagnosis
- **GIVEN** a CI-flake diagnosis request without write permission
- **WHEN** the reliability workflow runs
- **THEN** it MUST return evidence and classification only
- **AND** MUST NOT modify code, rerun CI, or push.

### Requirement: optional domain skills have explicit negative triggers

Every conditional UI, translation, archive, upgrade, recording and platform/forge overlay MUST have an explicit applicability predicate, prohibited contexts and unsupported-capability response. Common pstack MUST NOT automatically load domain packs irrelevant to the task.

#### Scenario: backend task on project without browser
- **GIVEN** a backend-only repository and a code-review task
- **WHEN** portable skill selection occurs
- **THEN** recording and browser rules MUST stay inactive
- **AND** ordinary correctness/security review MUST still proceed.

### Requirement: cleanup observes terminal settlement

Resource-owning tests MUST model cross-process/runner collision scope, register cleanup immediately, restore process-global state exactly, and await terminal settlement of subprocesses, servers, workers and streams. Platform-specific requirements MUST be observed or declared unavailable, never silently weakened.

#### Scenario: close call without quiescence
- **GIVEN** a fixture invoked `close()` but a child can still mutate shared state
- **WHEN** cleanup is evaluated
- **THEN** quiescence MUST NOT be reported until the child exits and effects settle.

### Requirement: candidate promotion has negative controls and rollback

Candidate changes MUST be evaluated using the existing blinded `eval` playbook plus independent checks. Promotion MUST require no observed critical safety regression, false PASS, known baseline correctness loss or forbidden activation in the covered corpus. Evaluation MUST report sample sizes and may yield INCONCLUSIVE instead of implying universal validity. Failing changes MUST be reverted or held for repair.

#### Scenario: shorter prompt causes missed verification
- **GIVEN** an optimized description reduces first-turn tokens but triggers extra rereads and misses required verification
- **WHEN** total work is compared
- **THEN** the shorter prompt MUST NOT be promoted on first-turn token savings alone.
