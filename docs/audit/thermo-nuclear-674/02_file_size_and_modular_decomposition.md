# 02: File Size and Modular Decomposition

- **Base Revision**: `66648081fbd7b4642f38ba0b273417a8891026ba`
- **Head Revision**: `676275f1dfa83857500b171f1a50a1dfd9a690bf`
- **Focus**: Verification of the 1,000-line ceiling (Rule 1) across all touched files, test decomposition, and module cohesion.

---

## 1. Line Count Audit (Rule 1 Compliance)

Rule 1 specifies: **Do not let a PR push a file from under 1k lines to over 1k lines without a very strong reason.**

An audit of all files modified or added between `6664808` and `676275f` confirms that **zero files exceed or approach the 1,000-line limit**:

| File Path | Base Lines | Head Lines | Delta | Status |
|:---|:---:|:---:|:---:|:---:|
| `scripts/decision_adapter.py` | 556 | 657 | +101 | PASS (< 700 lines) |
| `scripts/evidence_receipts.py` | 536 | 588 | +52 | PASS (< 600 lines) |
| `scripts/route_resolver.py` | 560 | 565 | +5 | PASS (< 600 lines) |
| `tests/test_paid_budget_concurrency.py` (New) | 0 | 271 | +271 | PASS (< 300 lines) |
| `tests/test_decision_bounded_invariants.py` | 114 | 121 | +7 | PASS (< 150 lines) |
| `tests/test_jev_mapping_and_calibrated_evidence.py` | 338 | 454 | +116 | PASS (< 500 lines) |
| `tests/test_advisory_promotion.py` | 298 | 322 | +24 | PASS (< 350 lines) |
| `tests/test_canonical_index.py` | 151 | 157 | +6 | PASS (< 200 lines) |
| `tests/test_class_calibration_policy.py` | 185 | 189 | +4 | PASS (< 200 lines) |
| `tests/test_jev_privacy_and_bypass.py` | 252 | 256 | +4 | PASS (< 300 lines) |

The highest line count among all touched modules is `scripts/decision_adapter.py` at 657 lines, providing a healthy 34% safety margin below the 1,000-line ceiling.

---

## 2. Test Suite Decomposition & Cohesion

In earlier PRs (e.g. #672), monolithic test files like `test_model_role_policy.py` (995 lines) were decomposed into smaller focused files. 

For the Epic #674 changes:
1. **Isolated Concurrency Verification**: Rather than appending multithreaded test cases and state-machine checkers into `tests/test_decision_adapter.py` (which would have expanded it past 800 lines), the concurrency suite was created as an independent module: [`tests/test_paid_budget_concurrency.py`](file:///home/tommyk/projects/pstack/tests/test_paid_budget_concurrency.py) (271 lines).
2. **Dedicated Invariant Checker**: The bounded router invariant tests live in [`tests/test_decision_bounded_invariants.py`](file:///home/tommyk/projects/pstack/tests/test_decision_bounded_invariants.py) (121 lines).
3. **Receipt & Mapping Separation**: Calibrated evidence validation is isolated in [`tests/test_jev_mapping_and_calibrated_evidence.py`](file:///home/tommyk/projects/pstack/tests/test_jev_mapping_and_calibrated_evidence.py) (454 lines).

---

## 3. Structural Decomposition Assessment

- **Single Responsibility Principle**:
  - `scripts/decision_adapter.py` owns semantic observation retrieval, provider profile definitions, and local spend tracking.
  - `scripts/evidence_receipts.py` owns cryptographic hash validation, receipt serialization, and threshold verification.
  - `scripts/route_resolver.py` owns pipeline orchestration without direct knowledge of wire protocols or transport details.
- **Decomposition Verdict**: UNCONDITIONAL PASS. No file decomposition is immediately required to satisfy the 1,000-line ceiling.
