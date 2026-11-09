# ADR-0022: Containment of JEV Fast-Worker Role Fit to PStack

- **Status**: Accepted
- **Deciders**: Tommy, PStack Core Maintainers
- **Date**: 2026-10-21
- **Context**: Issue #517 and Issue #670 explore extending System One semantic decision assistance to fast-worker role fit and leaf skill suggestions for QStack.

---

## Decision

1. **Strict PStack Containment**:
   All decision provider adapters, wire transports, role resolvers, and cryptographic evidence receipts shall reside exclusively in `pstack`.
   No decision routers, duplicate catalogs, or semantic registries shall be created in `qstack`. `qstack` remains a thin consumer of static profile exports and signed receipts.

2. **Catalog Confinement & Contract #429**:
   Candidate models must be sourced exclusively from actual host catalogs via `/setup-pstack`. Fabricated or hardcoded model identifiers are prohibited.

3. **Cognitive Tier Protection**:
   Frontier reasoning and verification roles (`architect`, `independent-verifier`, `arena-cross-judge-pool`, `judgment-and-prose`) cannot be demoted by semantic recommendations. Fast-worker role-fit is restricted exclusively to low-risk execution roles (`comment-sicko`, `how-explorer`, `why-investigators`, small `refactoring`).

4. **Shadow-First Holdout Validation**:
   All fast-worker semantic recommendations run in shadow mode until holdout benchmark replays prove net accuracy and cost benefits, recorded in `references/calibrated-evidence.json`.
