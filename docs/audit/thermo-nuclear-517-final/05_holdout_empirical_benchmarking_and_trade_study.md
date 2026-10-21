# Thermo-Nuclear Review: Holdout Empirical Benchmarking & Trade Study

> **2026-10-21 evidence correction:** All prices and end-to-end latencies presented below are **simulated** from constants in `scripts/eval_fast_role_task_fit.py` (12 predeclared task fixtures). The 21.3% and 16.1% modeled cost savings and 350.1/395.0ms modeled latencies are a deterministic **trade-study sensitivity analysis**, not observed live API spend, real provider roundtrips, wall-clock measurements, blinded independent field performance, or generalizable financial savings. Acceptance work: [#678](https://github.com/tommy-ca/pstack/issues/678). Do not use this simulation to authorize JEV advisory decisions or paid calls.


- **Subsystem**: Empirical Holdout Benchmarking & Model-Choice Trade Study  
- **Primary Source**: Issue [#517](https://github.com/tommy-ca/pstack/issues/517), [`scripts/eval_fast_role_task_fit.py`](https://github.com/tommy-ca/pstack/blob/66648081fbd7b4642f38ba0b273417a8891026ba/scripts/eval_fast_role_task_fit.py)  
- **Crosslinks**: `qstack#1786`, `qstack#1789`, `qstack#1790`, `qstack#1791`  
- **Base Revision**: `dea54d5cd723e06aa6a3afb78f9c3a79e82abb32`  
- **Head Revision**: `a737926189ea73dfcb3d1685764d8a57ba8d2f2b`  
- **Severity**: Empirical Measurement & Evaluation (Rule 4 & Rule 7)

---

## 1. Trade Study Overview & Methodology

Issue [#517](https://github.com/tommy-ca/pstack/issues/517) mandated an empirical comparison of three candidate approaches on real task fixtures before promoting any semantic model-choice advice:

1. **Baseline Policy (A)**: Shipped static model-role policy mapped from `pstack.package.json` and host tier defaults.
2. **Deterministic Routing (B)**: Purely deterministic task-feature routing based on diff lines, existing test coverage, and role risk classification.
3. **Semantic JEV (C)**: Opt-in closed-set suggestions from a System One provider, gated behind class thresholds and persisted calibrated evidence receipts.

### Holdout Task Fixture Corpus
The evaluation corpus in [`scripts/eval_fast_role_task_fit.py`](https://github.com/tommy-ca/pstack/blob/66648081fbd7b4642f38ba0b273417a8891026ba/scripts/eval_fast_role_task_fit.py#L97-L225) consists of 12 versioned tasks representing both core maintenance and quant trading workloads (from `qstack#1791`):

| Task ID | Domain | Role | Diff LOC | Tests | Consequence | Optimal Tier |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `core_comment_cleanup` | pstack-core | `comment-sicko` | 18 | Yes | Low | `fast-worker` |
| `core_how_subsystem_navigation` | pstack-core | `how-explorer` | 0 | Yes | Low | `fast-worker` |
| `core_why_commit_history` | pstack-core | `why-investigators` | 0 | Yes | Low | `fast-worker` |
| `core_small_refactor_date_helper` | pstack-core | `refactoring` | 35 | Yes | Low | `fast-worker` |
| `core_large_refactor_routing_pipeline` | pstack-core | `refactoring` | 480 | Yes | High | `strongest` |
| `core_architect_receipt_verification` | pstack-core | `architect-runners` | 220 | No | High | `panel` |
| `core_independent_verifier_diff` | pstack-core | `independent-verifier` | 65 | Yes | High | `strongest` |
| `quant_oms_order_parser_opt` | quant-domain | `refactoring` | 45 | Yes | Low | `fast-worker` |
| `quant_oms_risk_limits_audit` | quant-domain | `independent-verifier` | 85 | Yes | High | `strongest` |
| `quant_log_explorer` | quant-domain | `how-explorer` | 0 | Yes | Low | `fast-worker` |
| `quant_portfolio_covariance_refactor` | quant-domain | `refactoring` | 310 | Yes | High | `strongest` |
| `core_swarm_parallel_smoke` | pstack-core | `swarm-workers` | 12 | Yes | Low | `fast-verifier` |

---

## 2. Benchmark Execution Results

Executing `uv run python scripts/eval_fast_role_task_fit.py` on commit `a737926` yielded:

```text
============================================================================
FAST-WORKER ROLE & LEAF SKILL TASK-FIT HOLDOUT BENCHMARK
============================================================================
Host Catalog:             antigravity (Contract #429 Bound)
Total Holdout Tasks:      12 (4 Quant OMS holdouts)
Calibrated Evidence Gate: ACTIVE
----------------------------------------------------------------------------
Pipeline                     | Accuracy  | Optimal Fit | Total Cost | p50 Latency
----------------------------------------------------------------------------
Baseline Policy (A)          |    100.0% |       83.3% | $   0.1270 |    1200.0ms
Deterministic Routing (B)    |    100.0% |      100.0% | $   0.1000 |     350.1ms
Semantic JEV (C)             |    100.0% |       91.7% | $   0.1065 |     395.0ms
----------------------------------------------------------------------------
Deterministic vs Baseline Cost Savings: 21.3%
Semantic JEV vs Baseline Cost Savings:  16.1%
----------------------------------------------------------------------------
INVARIANT CHECKS:
  • Cognitive Frontier Demotions:   0 (MUST BE 0)
  • Unmapped Model Slugs:           0 (MUST BE 0)
  • Zero External Bloat:            PASS
============================================================================
```

---

## 3. Trade Study Analysis & Findings

### Finding 1: Deterministic Routing Outperforms Semantic Routing
- **Cost**: Deterministic routing achieves **21.3% cost reduction** across the holdout corpus by routing small refactorings (< 100 LOC) to `fast-worker`, compared to **16.1%** for Semantic JEV (which incurs $0.0005 decision overhead per query).
- **Latency**: Deterministic routing adds **0.1ms** routing overhead, yielding a **p50 latency of 350.1ms** (~70% faster than baseline's 1200ms). In contrast, Semantic JEV adds a **45ms roundtrip network overhead**, yielding a p50 latency of **395.0ms**.
- **Reliability & Privacy**: Deterministic routing requires zero API tokens, makes zero network calls, transmits zero context, and has zero downtime risk.

### Finding 2: Cognitive Frontier Protection is 100% Effective
Across all 12 tasks and both experimental pipelines, **zero demotions** of high-risk cognitive roles occurred. Attempted hostile demotions of `architect-runners` or `independent-verifier` were blocked and failed open to frontier models.

### Finding 3: Role for Semantic JEV
Semantic JEV assistance provides value primarily when task intent is ambiguous or unstructured prose where diff line counts cannot be statically predetermined. However, advisory promotion should strictly require pre-existing calibrated evidence in `references/calibrated-evidence.json`. In the absence of evidence, shadow observation remains the safest mode.
