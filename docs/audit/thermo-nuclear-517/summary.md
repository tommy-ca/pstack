# Thermo-Nuclear Code Quality Review: JEV Resilience Wave & Issue #517

- **Scope**: JEV Resilience Implementation (PRs #662, #665, #666, #667) & Issue [#517](https://github.com/tommy-ca/pstack/issues/517)
- **Base Revision**: `dea54d5cd723e06aa6a3afb78f9c3a79e82abb32`
- **Head Revision**: `804df416c1ec0ce9f6888fbf02a43fe9714c776a`
- **Verdict**: **CONDITIONAL PASS WITH REQUIRED REMEDIATIONS**

---

## Executive Summary

Over the recent resilience wave (`dea54d5..804df41`), four consecutive PRs successfully resolved critical security, privacy, wire protocol, and mapping drift defects in pstack's JEV decision plane:
- **PR #662**: Aligned harness documentation and validated canonical 0.15.29 schemas across all 6 host targets.
- **PR #665**: Implemented strict early egress bypasses and positive authorization for context transmission (#658).
- **PR #666**: Reconciled wire contracts to official dictionary-mapped `questions`/`answers` and enforced finite unit-interval validations with budget ceilings (#664, #660).
- **PR #667**: Updated canonical pins to upstream 0.15.29 (`88d47514`) and locked advisory route promotion behind persisted, pre-existing calibrated evidence receipts (#663, #659).

All functional requirements are met: 951+ offline tests pass, 8/8 rollback equivalence scenarios pass, and 12/12 routing evaluation fixtures match baseline truth.

However, an audit under the **Thermo-Nuclear Code Quality Standards** reveals that rapid defect remediation introduced noticeable procedural debt, conditional tangling, and impending file-size limit violations. In particular, core routing has sprawled into an 180-line procedural ladder, unit-interval validation is duplicated across adapter routines, and the model role policy test file sits at 995 lines—just 5 lines away from breaching the non-negotiable 1,000-line ceiling.

---

## Key Findings (Narrative Overview)

### Finding 1: Procedural Conditional Sprawl in Route Resolver (Rule 0 & Rule 2)
The function [`resolve_skill_order_with_shadow`](file:///home/tommyk/projects/pstack/scripts/route_resolver.py#L314-L494) has become a 180-line procedural conditional ladder containing 13 sequential inline checks and 14 separate return statements. It conflates egress gatekeeping, provider dispatch, and evidence vetting. Under Rule 0 (Code Judo) and Rule 2 (Eliminate Spaghetti Growth), this logic must be decoupled into three single-responsibility stages: `_is_egress_bypassed`, `_load_semantic_candidates`, and `_evaluate_advisory_promotion`.  
*Full Analysis & Worked Proposal*: [`01_route_resolver_pipeline_and_bypass_chain.md`](file:///home/tommyk/projects/pstack/docs/audit/thermo-nuclear-517/01_route_resolver_pipeline_and_bypass_chain.md).

### Finding 2: Duplicated Unit-Interval Validation & Repetitive Factory Calls (Rule 4 & Rule 6)
In [`scripts/decision_adapter.py`](file:///home/tommyk/projects/pstack/scripts/decision_adapter.py#L432-L557), strict finite validation of floats in `[0.0, 1.0]` is implemented with duplicate code blocks for `confidence` and `probabilities`. Additionally, the invalid observation structure is constructed verbatim 8 separate times in the parser. Extracting a pure `_parse_unit_interval` helper and an `_invalid_obs` factory simplifies parser control flow and eliminates 35 lines of boilerplate.  
*Full Analysis & Worked Proposal*: [`02_decision_adapter_validation_and_transport.md`](file:///home/tommyk/projects/pstack/docs/audit/thermo-nuclear-517/02_decision_adapter_validation_and_transport.md).

### Finding 3: Cryptographic Evidence Receipt Lifecycle Fragmentation (Rule 3 & Rule 5)
[`scripts/evidence_receipts.py`](file:///home/tommyk/projects/pstack/scripts/evidence_receipts.py) defines three critical receipts (`DecisionReceipt`, `CalibratedEvidenceReceipt`, `CheckEvidenceReceipt`). While their cryptographic integrity checks are robust, their serialization and deserialization implementations are fragmented: all three copy-paste `to_dict` and `to_json`, while deserialization ranges from manual 13-key procedural unpacking to raw `**kwargs` unpacking. A shared `ReceiptBase` mixin standardizes serialization, deserialization, and file loading across all receipts.  
*Full Analysis & Worked Proposal*: [`03_evidence_receipts_and_lifecycle_cohesion.md`](file:///home/tommyk/projects/pstack/docs/audit/thermo-nuclear-517/03_evidence_receipts_and_lifecycle_cohesion.md).

### Finding 4: Imminent 1,000-Line File Threshold Breach in Model Role Tests (Rule 1)
[`tests/test_model_role_policy.py`](file:///home/tommyk/projects/pstack/tests/test_model_role_policy.py) has grown to 995 lines across 47 tests. Rule 1 strictly forbids PRs from pushing files past 1,000 lines without decomposition. Adding test coverage for Issue #517 would immediately violate this rule. The test suite must be decomposed along cohesive architectural lines into `test_model_role_schema.py` (~250 lines), `test_model_role_constraints.py` (~380 lines), and `test_model_role_profiles.py` (~415 lines).  
*Full Analysis & Worked Proposal*: [`04_model_role_policy_test_decomposition.md`](file:///home/tommyk/projects/pstack/docs/audit/thermo-nuclear-517/04_model_role_policy_test_decomposition.md).

### Finding 5: Preservation of Strict PStack/QStack Boundary in Issue #517 (Rule 6)
Issue #517 explores extending JEV semantic decision assistance to best-fit fast worker roles and model choices for QStack. To prevent architecture drift and maintenance duplication, all JEV provider transport, host catalog resolution (Contract #429), and receipt verification must remain 100% inside `pstack`. `qstack` must remain a thin quant overlay consuming static profile exports with zero duplicate routers, registries, or catalogs. Role-fit extensions must remain shadow-only until backed by holdout benchmarks in `references/calibrated-evidence.json`.  
*Full Analysis & Boundary Architecture*: [`05_qstack_boundary_and_task_fit_architecture.md`](file:///home/tommyk/projects/pstack/docs/audit/thermo-nuclear-517/05_qstack_boundary_and_task_fit_architecture.md).

---

## Proposed Remediation Sequence

To implement these recommendations without disrupting existing workflows or risking regressions, we recommend executing three phased PR waves:

1. **Wave 1 (Refactor & Judo)**:
   - Apply the 3-stage pipeline refactoring to [`scripts/route_resolver.py`](file:///home/tommyk/projects/pstack/scripts/route_resolver.py).
   - Apply `_parse_unit_interval` and `_invalid_obs` to [`scripts/decision_adapter.py`](file:///home/tommyk/projects/pstack/scripts/decision_adapter.py).
   - Unify receipt serialization with `ReceiptBase` in [`scripts/evidence_receipts.py`](file:///home/tommyk/projects/pstack/scripts/evidence_receipts.py).
2. **Wave 2 (Test Decomposition)**:
   - Decompose `tests/test_model_role_policy.py` into schema, constraints, and profiles suites before adding any new role-fit tests.
3. **Wave 3 (Issue #517 Shadow Benchmarking)**:
   - Implement shadow fast-worker role suggestions using host catalogs under Contract #429.
   - Run holdout benchmarks against QStack replay tasks (`qstack#1791`) and generate calibrated receipts.

---

## Behavior Pin & Verification Record

All audit findings and code-judo proposals are verified against the following behavior pins:
- **Full Test Suite**: `uv run pytest` (951 passed)
- **Rollback Equivalence**: `uv run python scripts/verify_rollback_equivalence.py` (8/8 scenarios verified)
- **Routing Evaluation**: `uv run python scripts/eval_decision_routing.py` (12/12 fixtures verified)
