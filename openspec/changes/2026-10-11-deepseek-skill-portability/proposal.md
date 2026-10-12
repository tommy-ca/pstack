# DeepSeek-derived portable skill patterns

## Intent

Select reusable *behavioral invariants* from [DeepSeek Harness skills](https://github.com/deepseek-ai/deepseek-harness/tree/d743267388641bc76f17c45ce8b4c231aed1d32c/.agents/skills) and refine existing [pstack](https://github.com/tommy-ca/pstack) skills/playbooks instead of copying DeepSeek-specific wrappers. This change is **spec-only**: new issues authorize implementation, not this PR.

## Frozen evidence

- DeepSeek Harness master commit: `d743267388641bc76f17c45ce8b4c231aed1d32c`; 16 skill definitions plus references/scripts.
- Target pstack main at audit: `8f7a3c6d98aafcff4ab2f469df3784315dc36874`.
- Canonical discipline: [Cursor pstack](https://github.com/cursor/plugins/tree/main/pstack). The target repo's `UPSTREAM` pins pstack to tree `df581122cde17e6e27686b5a448bde23e4ad4318`.
- Source license: DeepSeek Harness MIT; retain attribution/license if substantial expression is reused. Prefer independent rewrites of behavioral contracts.
- Existing owners: #259 verification/scaffolding, #281 role/host boundary, #288 OMP-native proof, #303 route containment defect. Do not duplicate or assume they are complete.

## Why

DeepSeek's skill files demonstrate precise engineering rules around test isolation, error ownership, evidence, context and writing. Their presence and specificity demonstrate *documented project practice*, **not measured effectiveness or behavioral parity on all pstack hosts**. A generic skills import would couple pstack to DSH's pnpm/Vitest/Cordis, GitHub preview features, specific UI/locale trees, and credentials. Instead, reuse a narrow set of testable outcomes.

## Required outcomes

1. A source-pinned, all-16 decision crosswalk with current pstack owners and explicit exclusions.
2. A minimal semantic decomposition of task eligibility, context, resource/state, validation and evidence.
3. Existing playbooks remain the only orchestration layer; host-specific invocations remain in adapters/profiles.
4. A depth-first pilot of CI resource isolation + diff-scoped verification with deterministic red/green checks.
5. Follow-on error-state, exact-head review, simplification and context improvements only when evals justify them.
6. A truthful six-host acceptance matrix; offline static support must not be promoted to observed-live.

## Non-goals

No second skill registry/router, agent graph engine, scheduler, invented capability enum, DSH runtime dependency, universal git forge CLI, automatically required browser GIF, bilingual documentation, UI styling policy, or experimental GitHub stack protocol. No new claims of successful native OMP agent execution.

## Decision

Adopt **extend existing pstack owners** (option A). Option B, import 16 DSH skills under a parallel namespace, duplicates contracts and inflates routing ambiguity. Option C, rebuild skill runtime and verification infrastructure, violates KISS/YAGNI. Reassess an extra leaf skill only after evaluation proves an existing owner cannot express a behavior.

## What Changes

Spec-only: this change adds planning artifacts and one intent-driven delta spec. It ships no runtime, skill, profile or package behavior.

- **Source-pinned 16-skill inventory** — [evidence-matrix.md](evidence-matrix.md) crosswalks all sixteen DSH `SKILL.md` entries at `deepseek-ai/deepseek-harness@d7432673`, each with extracted invariant, one existing pstack owner and an explicit adopt/refine/defer decision.
- **Atomic patterns** — [atomic-patterns.md](atomic-patterns.md) decomposes the mapping into 20 observable behavior atoms (B01–B20) with positive/negative triggers, a single owner each and six compositional paths. Atomization is analytical; it instantiates no new classes.
- **Qualification schema** — [schemas/skill-pattern-qualification.schema.json](schemas/skill-pattern-qualification.schema.json) validates curatorial ledger records only. It does not change the router, package descriptor or four-plane receipt schema.
- **Baseline corpus** — [qualification-and-eval.md](qualification-and-eval.md) fixes the six-stage claim taxonomy, entry/recomposition/promotion gates, and the E01–E07 positive plus N01–N07 negative archetype corpus that must be measured before any candidate is compared.
- **Spec delta** — [specs/pstack-reusable-skill-patterns/spec.md](specs/pstack-reusable-skill-patterns/spec.md) adds requirements for source provenance, one route and one owner, deferred discovery, test-resource lifecycle, changed-head currency, typed failure, simplification and honest evidence.
- **Follow-ups** — review and prose refinements (#313) and conditional domain packs (#314) stay deferred until the resource-lifecycle (#311) and changed-head currency (#312) pilots hold; candidate improvements count only against the frozen baseline corpus.
- **Gate matrix** — the seven-dimension qualification matrix (task correctness, selection precision, safety and effect integrity, evidence honesty, context economy, maintenance economy, host applicability) with the three-tier / four-plane evidence gates defines promotion, block and rollback conditions.

## Tracking

Epic #305 → sub-epics #306 (spec/eval) and #307 (implementation/acceptance) → leaves #308–#315. Specification is preliminary; all implementation/live claims are untested until the linked work executes.

## Second-pass qualification amendment

A documented upstream technique is a **candidate**, not an already-proven pstack improvement. The source-to-pstack mapping is revised by [atomic-patterns.md](atomic-patterns.md) (20 logical behavior atoms) and [qualification-and-eval.md](qualification-and-eval.md) (claim stages, organic task corpus, negative triggers, repeatability). [schemas/skill-pattern-qualification.schema.json](schemas/skill-pattern-qualification.schema.json) describes the *documentation ledger*, not a new runtime adapter schema.

**Promotion rule:** require an eligible task, a single existing pstack owner, observable improvement or justified parity, negative controls, no safety/evidence regressions, and cross-project evidence scoped to named archetypes. Never claim source-documented guidance alone is proven across project classes. Do not instantiate atomic vocabulary as a new engine.

**Gate dependencies:** #310 collects baseline measurements before #311/#312 and evaluates candidate changes afterward; #315 aggregates completed behavioral evidence and independently reports unavailable native hosts. No duplicate task or new epic is warranted.
