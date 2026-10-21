# Fast-Worker Role & Leaf Skill Task-Fit Proposal

- **Tracking Issues**: tommy-ca/pstack#517, tommy-ca/pstack#670
- **Crosslinks**: tommy-ca/qstack#1786, tommy-ca/qstack#1789, tommy-ca/qstack#1790, tommy-ca/qstack#1791

## Why

Following the JEV resilience wave (PRs #662, #665, #666, #667), pstack's System One decision plane possesses verified egress guards, canonical mapping drift gates, and receipt-locked advisory promotion.
Issue #517 explores extending semantic decision assistance to best-fit fast worker roles and leaf skill suggestions for QStack workflows.

However, strict architectural discipline mandates:
1. **Zero Bloat to QStack**: All decision transports, role resolution algorithms, host catalog bindings, and cryptographic evidence receipts remain 100% inside `pstack`. `qstack` remains a thin quant overlay consuming static profile exports.
2. **Catalog Confinement (Contract #429)**: Candidate models evaluated for role fit must be sourced exclusively from actual host catalogs via `/setup-pstack`. No hard-coded, synthetic, or invented model slugs are permitted.
3. **Cognitive Tier Protection**: High-risk roles (`architect-runners`, `arena-cross-judge-pool`, `independent-verifier`, `judgment-and-prose`) remain strictly pinned to configured frontier models. JEV semantic recommendations CANNOT demote them.
4. **Holdout Benchmarking Before Promotion**: Fast-worker role recommendations remain in shadow mode until empirically verified against holdout task replay fixtures and signed into `references/calibrated-evidence.json`.

## What Changes

1. Ground eligible fast-worker roles (`comment-sicko`, `how-explorer`, `why-investigators`, `refactoring`) and eligible leaf skill suggestion taxonomy in `pstack`.
2. Provide a benchmark suite (`scripts/eval_fast_role_task_fit.py`) comparing:
   - (A) Existing role/model policy baseline
   - (B) Purely deterministic task features and budget routing
   - (C) Opt-in closed-set JEV suggestions for low-risk fast workers
3. Provide unit and regression tests in `tests/test_fast_role_task_fit.py` asserting non-demotion of cognitive roles, catalog confinement, and receipt gating.

## Non-Goals

- No duplicate routers, catalogs, or registries in `qstack`.
- No live runtime model dispatch from the pure planner.
- No unproved advisory promotion without holdout calibration evidence.
