# Fast-Worker Role & Leaf Skill Task-Fit Tasks

- **Tracking Issues**: tommy-ca/pstack#517, tommy-ca/pstack#670
- **Crosslinks**: tommy-ca/qstack#1786, tommy-ca/qstack#1789, tommy-ca/qstack#1790, tommy-ca/qstack#1791

---

## 1. Specification & Design Grounding

- [x] Ground fast-worker role fit within `pstack` with zero bloat to `qstack` (`proposal.md`, `design.md`, `adr.md`).
- [x] Pin high-risk cognitive roles (`architect-runners`, `arena-cross-judge-pool`, `arena-runners`, `independent-verifier`, `judgment-and-prose`, `feature`, `hardest-tasks`) to frontier models.
- [x] Ground low-risk fast-worker candidate set (`comment-sicko`, `how-explorer`, `why-investigators`, `refactoring`).
- [x] Enforce Contract #429 catalog confinement (all candidate model identifiers must exist in host catalog).

---

## 2. Implementation: Fast-Worker Task-Fit & Holdout Evaluator

- [x] Implement `scripts/eval_fast_role_task_fit.py`:
  - [x] Holdout task fixture corpus with QStack replay/OMS tasks and general maintenance tasks.
  - [x] Three candidate pipelines:
    - (A) Baseline model-role policy (`profiles/<host>.json`).
    - (B) Deterministic task-feature & budget routing.
    - (C) Opt-in closed-set JEV suggestions for fast-worker roles.
  - [x] Non-demotion gate preventing cognitive frontier demotion.
  - [x] Measurement of route status, task success, latency (ms), and cost (USD).
  - [x] Summary report and calibrated evidence generation.

---

## 3. Verification & Test Suite

- [x] Implement unit and regression tests in `tests/test_fast_role_task_fit.py`:
  - [x] Test cognitive role non-demotion invariant.
  - [x] Test catalog confinement (rejection of unmapped / invented slugs).
  - [x] Test eligible fast-worker role constraints and diff-size thresholds.
  - [x] Test holdout benchmark metrics and receipt verification.
  - [x] Strict compliance with Rule 1 (< 500 lines).
- [x] Run full test suite:
  - [x] `uv run pytest -q tests/test_fast_role_task_fit.py`
  - [x] `uv run python scripts/eval_fast_role_task_fit.py`
  - [x] `uv run python scripts/verify_rollback_equivalence.py`
  - [x] `uv run python scripts/eval_decision_routing.py`

---

## 4. Packaging, Verification & Ship

- [x] Commit changes to `feat/jev-fast-worker-task-fit` (landed as `a737926` via PR #673, merged 2026-10-21).
- [x] Push branch and open PR for Issue #670 (PR #673, MERGED).
- [x] Dispatch `independent-verifier-exec` to independently verify diff and test execution (post-implementation thermo review recorded in `6664808`).
- [x] Merge PR into `main` and close Issue #670 (CLOSED).
- [x] Update Issue #517 with holdout evaluation findings and complete goal (both #517 and #670 CLOSED).
