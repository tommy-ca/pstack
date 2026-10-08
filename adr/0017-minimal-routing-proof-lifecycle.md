# ADR 0017: Minimal Routing, Proof, and Lifecycle Architecture

## Context

Issue #235 and its sub-issues identified key hardening requirements across the portability stack:
1. Routing: Five drivers (`grok`, `codex`, `omp`, `opencode`, `antigravity`) duplicated substring matching (`playbook in need.lower()`), leading to false PASS verdicts, while `profiles/*.json` referenced non-existent skill paths (`prove-it-works`) or unmapped agent IDs (`pstack:how-explorer`).
2. Verification: Scenario reduction masked `FAIL` behind `BLOCKED`, subprocesses lacked timeouts, and static profile checks were reported as runtime PASS.
3. Package Lifecycle: Unmanaged files inside plugin directories were deleted indiscriminately by `copy_skills` and `uninstall_plugin`.

In Issue #242, an Arena evaluation was conducted to decide among three architectural options:

- **Candidate A (Patch Each Driver Locally):**
  Apply isolated bug fixes directly into each of the 6 driver implementations and verifier methods.
- **Candidate B (Pure Shared Resolver, Explicit Proof Tiers & Lossless Lifecycle Guard):**
  Extract a pure, typed route matcher in `scripts/route_resolver.py`; introduce a strict severity lattice (`FAIL > BLOCKED > UNTESTED > PASS`) with explicit evidence levels (`static`, `offline`, `observed_live`); implement preflight manifest/ownership checks in `scripts/package-lifecycle.py`.
- **Candidate C (Generic Workflow Orchestration Framework):**
  Introduce a full-blown plugin orchestration and event-scheduling engine.

## Evaluation & Interrogate Review

- **Candidate A was rejected**: Violates DRY and foundational consistency. Six independent driver implementations would inevitably drift, and edge-case handling (ambiguity, case sensitivity, fallback policy) would duplicate across all harnesses.
- **Candidate C was rejected**: Violates YAGNI, Laziness Protocol, and Foundational Thinking. A general-purpose workflow scheduler introduces large runtime dependencies, higher state overhead, and extensive migration surface without solving the concrete domain issues.
- **Candidate B was selected**: Provides one deterministic contract for routing and evidence semantics while respecting host-specific precedence in native drivers. It minimizes reader load, keeps business logic testable offline, and maintains clean system boundaries.

## Decision

1. Extract a pure typed `RouteResolver` in `scripts/route_resolver.py` that matches whole identifiers or explicit aliases, returning `RouteResolution(status, target_kind, target_path, id)`.
2. Wire all six host drivers to the shared resolver while preserving native precedence (such as Droid's advisory / shadow / project-vs-plugin precedence).
3. Reconcile profile target references (`principle-prove-it-works`, `agents/how-explorer.md`, and clean Codex command separation).
4. Enforce failure-first reduction (`FAIL > BLOCKED > UNTESTED > PASS`) and bounded subprocess execution with timeouts in `scripts/verify-portable.py`.
5. Require explicit evidence levels (`static`, `offline`, `observed_live`) on scenario results, ensuring static checks cannot satisfy live runtime proof.
6. Guard package lifecycle operations against destroying unmanaged or foreign files inside plugin trees.

## Status

Accepted.
