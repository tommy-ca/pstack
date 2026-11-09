# Fast-Worker Role & Leaf Skill Task-Fit Architecture & Design

- **Status**: Accepted (Shadow Evaluation Phase)
- **Primary Seam**: [`scripts/model_role_resolver.py`](file:///home/tommyk/projects/pstack/scripts/model_role_resolver.py), [`scripts/route_resolver.py`](file:///home/tommyk/projects/pstack/scripts/route_resolver.py)

---

## 1. Domain Model & Boundary Discipline

```
┌───────────────────────────────────────────────────────────────┐
│                        pstack (Host)                          │
│                                                               │
│   ┌───────────────────────────┐   ┌─────────────────────────┐ │
│   │ scripts/route_resolver.py │   │scripts/decision_adapter │ │
│   └─────────────┬─────────────┘   └────────────┬────────────┘ │
│                 │                              │              │
│                 ▼                              ▼              │
│   ┌───────────────────────────┐   ┌─────────────────────────┐ │
│   │  model_role_resolver.py   │◄──┤  references/calibrated- │ │
│   │ (Catalog-bound planning)  │   │      evidence.json      │ │
│   └─────────────┬─────────────┘   └─────────────────────────┘ │
└─────────────────┼─────────────────────────────────────────────┘
                  │ Static Model Plans & Exported Receipts
                  ▼
┌───────────────────────────────────────────────────────────────┐
│                       qstack (Consumer)                       │
│                                                               │
│   - Thin quantitative trading and research overlay only       │
│   - ZERO duplicate routers, catalogs, or registries           │
│   - Consumes role profiles & calibrated receipts statically   │
│   - Replay tasks/OMS holdouts used strictly for evaluation    │
└───────────────────────────────────────────────────────────────┘
```

### Inviolable Invariants
1. **Host Catalog Bound (Contract #429)**: Candidate model slugs must be present in the target host's `model_catalog` in `profiles/<host>.json` (or host configuration).
2. **Cognitive Role Protection**: High-risk cognitive roles are immutable:
   - `architect-runners`: `panel`
   - `arena-cross-judge-pool`: `panel`
   - `independent-verifier`: `strongest`
   - `judgment-and-prose`: `strongest`
   - `feature`: `strongest`
   - `hardest-tasks`: `strongest`
   Semantic suggestions cannot demote these roles to lower-tier or unverified models.
3. **Eligible Fast-Worker Roster**:
   - `comment-sicko` (default: `fast-worker`)
   - `how-explorer` (default: `fast-worker`)
   - `why-investigators` (default: `fast-worker`)
   - `refactoring` (eligible for fast-worker tier on small diffs < 100 LOC with complete test coverage)

---

## 2. Evaluation Strategy & Trade Study

The evaluation harness evaluates three candidate approaches across holdout task fixtures:
- **Baseline (A)**: Host-tier default models mapped from `pstack.package.json`.
- **Deterministic (B)**: Task property extraction (line count, AST depth, file count, test presence) to select model tier deterministically.
- **Semantic JEV (C)**: Opt-in closed-set suggestion from System One provider, bounded within `[0.0, 1.0]` confidence and gated behind `references/calibrated-evidence.json`.

Metrics collected per task:
1. `route_status`: `PLANNED`, `DEGRADED`, or `BLOCKED`.
2. `task_success`: Binary success against test assertions.
3. `latency_ms`: Total execution time including decision provider roundtrip.
4. `cost_usd`: Cumulative API spend.
