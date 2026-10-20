# Thermo-Nuclear Review: QStack Boundary & Task-Fit Architecture

- **Subsystem**: Cross-Repository Architectural Boundary & Role-Fit Extension  
- **Primary Source**: Issue [#517](https://github.com/tommy-ca/pstack/issues/517), [`scripts/model_role_resolver.py`](file:///home/tommyk/projects/pstack/scripts/model_role_resolver.py), [`scripts/route_resolver.py`](file:///home/tommyk/projects/pstack/scripts/route_resolver.py)  
- **Base Revision**: `dea54d5cd723e06aa6a3afb78f9c3a79e82abb32`  
- **Head Revision**: `804df416c1ec0ce9f6888fbf02a43fe9714c776a`  
- **Severity**: Major (Boundary Leakage & Role-Fit Scope Discipline)

---

## 1. Problem Statement & Code Quality Diagnosis

Issue [#517](https://github.com/tommy-ca/pstack/issues/517) explores extending JEV semantic decision assistance to **best-fit fast worker roles and model choices** for QStack workflows. 

However, under **Rule 6 (Keep logic in the canonical layer; prevent architectural drift)** and the user mandate:
> *"keep the jev integration lean and clean, do not bloat to qstack, keep it at pstack"*,

there is a severe risk of architectural sprawl if the boundary between `pstack` and `qstack` is not rigorously formalized:
1. **Risk of Duplicate Registries**: Creating duplicate decision routers, taxonomy maps, or model catalogs in `qstack` would create synchronization drift, double maintenance overhead, and split brain routing.
2. **Unproved Promotion Risk**: Allowing JEV suggestions to dynamically select worker models without pre-existing holdout calibration would violate the core resilience invariants established in PR #667 and Issue #659.
3. **High-Risk Role Degradation**: Allowing semantic routing to down-select low-tier models for high-risk cognitive roles (`architect-runners`, `independent-verifier`, `arena-cross-judge-pool`) would compromise verification integrity.

---

## 2. Consumer Reachability & Cross-Repo Boundary Pin

### Concrete Boundary Division

```
┌─────────────────────────────────────────────────────────────┐
│                       pstack (Host)                         │
│                                                             │
│  ┌────────────────────────┐    ┌─────────────────────────┐  │
│  │ scripts/route_resolver │    │scripts/decision_adapter │  │
│  └───────────┬────────────┘    └────────────┬────────────┘  │
│              │                              │               │
│              ▼                              ▼               │
│  ┌────────────────────────┐    ┌─────────────────────────┐  │
│  │model_role_resolver.py  │◄───┤  references/calibrated- │  │
│  │(Catalog-bound planning)│    │     evidence.json       │  │
│  └───────────┬────────────┘    └─────────────────────────┘  │
└──────────────┼──────────────────────────────────────────────┘
               │ Pure Static Exports & CLI
               ▼
┌─────────────────────────────────────────────────────────────┐
│                      qstack (Consumer)                      │
│                                                             │
│  - Thin quant overlay only                                  │
│  - ZERO duplicate routers, catalogs, or registries          │
│  - Consumes role profiles & calibrated receipts statically  │
│  - Replay tasks/OMS holdouts used strictly for evaluation   │
└─────────────────────────────────────────────────────────────┘
```

### Inviolable Boundary Rules
1. **Zero JEV / Router Bloat in `qstack`**: `qstack` must not contain decision transports, provider SDK adapters, or duplicate routing logic. All semantic decision plumbing lives exclusively in `pstack`.
2. **Catalog Confinement (Contract #429)**: Candidate models evaluated for role fit must be sourced exclusively from real host catalogs via `/setup-pstack`. No hard-coded, synthetic, or invented model slugs are permitted.
3. **Strict Panel & Family Diversity**: For panel roles (`arena-runners`, `arena-cross-judge-pool`), family independence invariants cannot be waived or overridden by JEV recommendations.
4. **Cognitive Tier Protection**: High-risk roles (`architect`, `independent-verifier`, `judgment-and-prose`) are strictly pinned to configured frontier/high-capability models. Fast-worker role-fit is restricted exclusively to low-risk execution roles (e.g. `comment-sicko`, `refactoring`, `deslop`, `why-investigators`).

---

## 3. The "Code Judo" Architecture for Issue #517

Rather than adding a whole new routing pipeline or creating bespoke fast-role decision trees, we employ a "Code Judo" design that reuses existing pstack primitives:

### A. Reuse `scripts/model_role_resolver.py`
Fast worker role-fit is expressed as a pure configuration profile in `profiles/*.json` and planned via `scripts/model_role_resolver.py`. The resolver already enforces:
- Host catalog verification status (`clean`, `stale`, `unproven`)
- Per-role capability constraints
- Explicit override precedence

### B. Shadow-Only Evaluation Pipeline
Before any role-fit recommendation can be promoted:
1. Candidate model choices are recorded in shadow mode.
2. Holdout replay benchmarks (using QStack tasks from `qstack#1791`) measure:
   - Task completion accuracy
   - Total latency (including decision overhead)
   - Cost in USD
3. A `CalibratedEvidenceReceipt` is generated and signed off under `references/calibrated-evidence.json`.
4. Only when empirical holdout metrics prove net value over the deterministic baseline is advisory promotion enabled.

---

## 4. Net Maintained Obligation & Verification Plan

### Maintained Obligation Avoided
- Prevents introducing duplicate routing codebases across two repositories.
- Keeps QStack focused purely on quantitative research and trading pipelines.
- Reuses 100% of PStack's existing 113 JEV contract tests and 8 rollback equivalence scenarios.

### Recheck Commands
```bash
# Verify pstack model role contracts remain intact
uv run pytest -q tests/test_model_role_policy.py
uv run python scripts/verify_rollback_equivalence.py

# Verify zero qstack bloat / drift
git status
```
