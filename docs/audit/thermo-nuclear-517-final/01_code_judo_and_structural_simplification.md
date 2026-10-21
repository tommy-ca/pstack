# Thermo-Nuclear Review: Code Judo & Structural Simplification

- **Subsystem**: Core Decision Pipeline & Fast-Worker Task-Fit  
- **Primary Sources**: [`scripts/route_resolver.py`](file:///home/tommyk/projects/pstack/scripts/route_resolver.py), [`scripts/decision_adapter.py`](file:///home/tommyk/projects/pstack/scripts/decision_adapter.py), [`scripts/evidence_receipts.py`](file:///home/tommyk/projects/pstack/scripts/evidence_receipts.py), [`scripts/eval_fast_role_task_fit.py`](file:///home/tommyk/projects/pstack/scripts/eval_fast_role_task_fit.py)  
- **Base Revision**: `dea54d5cd723e06aa6a3afb78f9c3a79e82abb32`  
- **Head Revision**: `a737926189ea73dfcb3d1685764d8a57ba8d2f2b`  
- **Severity**: Comprehensive Assessment (Rule 0 & Rule 3)

---

## 1. Problem Diagnosis & Motivation

During the initial JEV resilience wave (PRs #662, #665, #666, #667), rapid patching of security and wire protocol gaps introduced severe procedural debt. Critical functions grew into monolithic conditional ladders where egress bypasses, provider network calls, candidate discovery, and receipt cryptographic validation were interleaved across dozens of lines of imperative control flow.

Under **Rule 0 (Be ambitious about structural simplification)** and **Rule 3 (Bias toward cleaning the design, not just accepting working code)**, code that works correctly is not sufficient. Code must be structured so that moving pieces disappear, abstractions earn their keep, and the control flow feels inevitable in hindsight.

---

## 2. Code Judo Moves Executed in Waves 1–3

### A. Decoupling Route Resolution into a 3-Stage Pipeline (PR #671)
In [`scripts/route_resolver.py`](file:///home/tommyk/projects/pstack/scripts/route_resolver.py), the function `resolve_skill_order_with_shadow` previously sprawled across 180 lines with 13 inline conditionals and 14 disparate return points. 

The Code Judo restructuring factored this flow into three pure, single-responsibility helper stages:
1. `_is_egress_bypassed`: Evaluates caller explicit commands, slash commands, direct needs, and System-Two playbooks in zero I/O time without constructing providers or sending bytes.
2. `_load_semantic_candidates`: Encapsulates cached reads of `references/decision-routing.json` and canonical mapping pins, isolating drift detection.
3. `_evaluate_advisory_promotion`: Consolidates confidence calibration, winner margin checks, provider/model identity matching, and receipt validity checks into an atomic gate.

This restructuring reduced `resolve_skill_order_with_shadow` from 180 lines of tangled branching down to ~80 lines of clean linear execution. All 8 rollback equivalence scenarios and 12 decision routing fixtures continue to pass with zero behavioral delta.

### B. Unit-Interval Parsing & Invalid Observation Factory (PR #671)
In [`scripts/decision_adapter.py`](file:///home/tommyk/projects/pstack/scripts/decision_adapter.py), parsing responses from System One providers required validating that floats for confidence and probabilities were finite numbers in `[0.0, 1.0]`, explicitly rejecting boolean types. Previously, 25 lines of duplicate float and range checks were copy-pasted across `confidence` and `probabilities` parsing, and the fallback invalid observation structure was instantiated verbatim 8 times.

Extracting a pure helper `_parse_unit_interval` and an internal factory method `self._invalid_obs` deleted ~35 lines of duplicate boilerplate, eliminated incidental branching, and guaranteed consistent validation semantics across all provider response fields.

### C. Polymorphic Receipt Lifecycle Consolidation (PR #671)
In [`scripts/evidence_receipts.py`](file:///home/tommyk/projects/pstack/scripts/evidence_receipts.py), three distinct cryptographic receipts (`DecisionReceipt`, `CalibratedEvidenceReceipt`, `CheckEvidenceReceipt`) independently implemented `to_dict`, `to_json`, and varying flavors of deserialization. 

Introducing `ReceiptBase` as a frozen mixin consolidated serialization and safe deserialization (with automatic field filtering) across all three receipt types. This eliminated duplicate boilerplate while making receipt serialization structurally identical across the codebase.

### D. Deterministic Fast-Worker Task-Fit (PR #673)
In implementing Issue [#517](https://github.com/tommy-ca/pstack/issues/517) and [#670](https://github.com/tommy-ca/pstack/issues/670) via [`scripts/eval_fast_role_task_fit.py`](file:///home/tommyk/projects/pstack/scripts/eval_fast_role_task_fit.py), rather than bolting a dynamic runtime model dispatch mechanism or external framework onto pstack, the implementation adhered strictly to static planning via [`scripts/model_role_resolver.py`](file:///home/tommyk/projects/pstack/scripts/model_role_resolver.py).

The evaluator demonstrated that a purely deterministic task-feature routing approach (inspecting diff lines, test coverage, and role risk) outperforms semantic LLM decision routing on cost and latency:
- **Cost**: 21.3% cost reduction vs baseline (compared to 16.1% for semantic JEV).
- **Latency**: 0.0ms decision overhead (compared to 45.0ms roundtrip overhead for semantic JEV).
- **Zero Dependencies**: Requires zero external SDKs, zero runtime frameworks, and zero network calls.

---

## 3. Consumer Reachability & Behavior Pin

- **Reachable Surfaces**: All public APIs in `scripts/route_resolver.py` (`resolve_skill_order`, `resolve_skill_order_with_shadow`), `scripts/decision_adapter.py` (`JevDecisionAdapter`, `ProviderObservation`), and `scripts/evidence_receipts.py` were preserved without signature regressions.
- **Behavior Pin**: 
  - `uv run pytest -q tests/test_route_resolver.py tests/test_decision_adapter.py tests/test_evidence_receipts.py tests/test_fast_role_task_fit.py` (217 passed).
  - `uv run python scripts/verify_rollback_equivalence.py` (8/8 passed).
  - `uv run python scripts/eval_decision_routing.py` (12/12 passed, 100% accuracy).

---

## 4. Net Maintained Obligation

- **Obligations Deleted**:
  - Eliminated 14 duplicate return points in `route_resolver.py`.
  - Deleted repetitive manual float parsing in `decision_adapter.py`.
  - Eliminated copy-pasted `to_dict` and `to_json` serialization routines across receipts.
  - Eliminated the need for a secondary decision router in QStack.
