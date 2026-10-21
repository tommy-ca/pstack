# Thermo-Nuclear Review: File Size & Modular Decomposition

- **Subsystem**: Repository File Structure & Test Suites  
- **Primary Sources**: [`tests/test_model_role_*.py`](file:///home/tommyk/projects/pstack/tests/), [`scripts/eval_fast_role_task_fit.py`](file:///home/tommyk/projects/pstack/scripts/eval_fast_role_task_fit.py), [`tests/test_fast_role_task_fit.py`](file:///home/tommyk/projects/pstack/tests/test_fast_role_task_fit.py)  
- **Base Revision**: `dea54d5cd723e06aa6a3afb78f9c3a79e82abb32`  
- **Head Revision**: `a737926189ea73dfcb3d1685764d8a57ba8d2f2b`  
- **Severity**: Critical Standard Enforcement (Rule 1)

---

## 1. Problem Diagnosis: The 1,000-Line Ceiling (Rule 1)

**Rule 1** states:
> *"Do not let a PR push a file from under 1k lines to over 1k lines without a very strong reason. Prefer extracting helpers, subcomponents, modules, or local abstractions instead of letting a file sprawl past 1000 lines."*

Prior to Wave 2, [`tests/test_model_role_policy.py`](file:///home/tommyk/projects/pstack/tests/test_model_role_policy.py) had grown to **995 lines**. It combined schema validation, capability constraint checking, host profile discovery parsing, and role resolver planning tests in a single monolithic file. Adding fast-worker task-fit tests or role-choice test coverage directly into this file would have immediately breached the 1,000-line ceiling.

---

## 2. Decomposition Strategy & Results

In **PR #672 (Wave 2)**, the monolithic test file was completely decomposed along cohesive architectural domains into four focused modules, each strictly respecting the 500-line boundary:

```
tests/test_model_role_policy.py (995 lines) [DELETED]
  ├── tests/model_role_helpers.py           (86 lines)  - Shared test fixtures & policies
  ├── tests/test_model_role_schema.py      (195 lines)  - Draft 2020-12 schema conformance
  ├── tests/test_model_role_constraints.py (244 lines)  - Role constraints & capability gates
  └── tests/test_model_role_profiles.py    (497 lines)  - Host catalog planning & wire export
```

In **PR #673 (Wave 3)**, the new fast-role holdout evaluator and test suite were authored with strict file size bounds:
- [`scripts/eval_fast_role_task_fit.py`](file:///home/tommyk/projects/pstack/scripts/eval_fast_role_task_fit.py): **561 lines** (including 12 detailed holdout fixtures, three evaluation pipelines, and formatted CLI output).
- [`tests/test_fast_role_task_fit.py`](file:///home/tommyk/projects/pstack/tests/test_fast_role_task_fit.py): **214 lines** (invariant assertions, catalog confinement, and boundary tests).

---

## 3. Repository File Size Audit (Current State @ `a737926`)

A full line count audit of all Python scripts and test files in `pstack` confirms that **zero files exceed 1,000 lines**:

| Rank | Path | Line Count | Status (<1,000 ceiling) |
| :--- | :--- | :--- | :--- |
| 1 | `scripts/prove-omp-vertical-slice.py` | 852 | PASS |
| 2 | `scripts/eval_blinded_pstack.py` | 826 | PASS |
| 3 | `tests/test_omp_rpc.py` | 822 | PASS |
| 4 | `scripts/project-package.py` | 797 | PASS |
| 5 | `tests/test_evidence_settlement.py` | 762 | PASS |
| 6 | `tests/test_surface_cache.py` | 709 | PASS |
| 7 | `scripts/package-lifecycle.py` | 695 | PASS |
| 8 | `tests/test_refresh_hygiene.py` | 665 | PASS |
| 9 | `scripts/portability_types.py` | 664 | PASS |
| 10 | `tests/test_verify_portable.py` | 639 | PASS |
| 11 | `tests/test_swarm_partition.py` | 625 | PASS |
| 12 | `tests/test_verify_harness.py` | 595 | PASS |
| 13 | `scripts/prove-omp-native-package.py` | 589 | PASS |
| 14 | `tests/test_evidence_durability.py` | 585 | PASS |
| 15 | `scripts/decision_adapter.py` | 584 | PASS |
| 16 | `scripts/verify-portable.py` | 576 | PASS |
| 17 | `scripts/eval_fast_role_task_fit.py` | 561 | PASS |
| 18 | `scripts/route_resolver.py` | 560 | PASS |
| 19 | `scripts/evidence_receipts.py` | 552 | PASS |
| 20 | `tests/test_shipping_safety.py` | 524 | PASS |
| 21 | `tests/test_portability_schemas.py` | 524 | PASS |
| 22 | `scripts/select_checks.py` | 517 | PASS |
| 23 | `scripts/verify-harness.py` | 506 | PASS |
| 24 | `tests/test_host_identity.py` | 502 | PASS |
| 25 | `scripts/canonical-index.py` | 499 | PASS |
| 26 | `tests/test_model_role_profiles.py` | 497 | PASS |
| 27 | `scripts/sync-antigravity-plugin.py` | 489 | PASS |
| 28 | `scripts/verify_rollback_equivalence.py` | 487 | PASS |
| 29 | `scripts/surface_revisions.py` | 453 | PASS |
| 30 | `tests/test_fast_role_task_fit.py` | 214 | PASS |

---

## 4. CI Workflow Integration

The decomposed test files and new fast-role test suite were integrated into [.github/workflows/portability-offline.yml](file:///home/tommyk/projects/pstack/.github/workflows/portability-offline.yml) and [`scripts/select_checks.py`](file:///home/tommyk/projects/pstack/scripts/select_checks.py):
- Check selection rules map changes in `scripts/` to the decomposed test modules.
- CI offline gate executes all decomposed suites hermetically.
- Zero test coverage was lost; 100% of the original 47 model-role policy tests and 6 new fast-role tests pass.
