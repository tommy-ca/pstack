# Cross-Port Semantic Atoms Analysis (2026-11-06)

## Overview & Frozen Source Pins

This analysis curates the atomic semantic building blocks derived from the three-source audit across:
1. **Canonical**: `cursor/plugins@c742dd61706fbacc1b95f1a20b7b988cf096ce6c` (2026-10-27, v0.15.36).
2. **Comparator**: `michael-denyer/pstack-claude@d88063f3355a5ecff0e6dbb890a11bab4b08bc2e` (2026-11-05, v0.9.130).
3. **Target Base**: `tommy-ca/pstack@5d58283f40f7fc8f56a536946abe79418538fe6e` (v0.15.29-preview.0).

Raw ingest digest: `5f58cac149ce46980e0367ffb5bdd0a05cb0cd81453d31aee40fb0b5f5bcd663` ([cross-port-semantic-delta-2026-11-06.md](../../raw/sources/cross-port-semantic-delta-2026-11-06.md)).

Links:
- [LLM Wiki Project Knowledge](../concepts/llm-wiki-project-knowledge.md)
- [Review Semantics & Verification](../concepts/review-semantics-and-verification.md)
- [Semantic Blocks & Crosswalk](../concepts/semantic-blocks-and-crosswalk.md)

---

## 11 Curated Cross-Port Semantic Atoms

### 1. Intent Routing
- **Status**: Source-based (canonical) & Observed (6 hosts).
- **Semantics**: User brief maps directly to a discrete skill or role without intermediate persistent routing daemon. Reconciled in `skills/poteto-mode/SKILL.md`.

### 2. Policy Principles
- **Status**: Source-based (canonical).
- **Semantics**: 24 immutable principles (KISS, YAGNI, SOLID, lazy execution). Comparator rewrites are audited; policy forks are isolated.

### 3. Playbook Composition
- **Status**: Source-based (canonical).
- **Semantics**: 22 named playbooks plus `opening-a-pr`. Orchestrate is agentic; no external `orch` binary dependency.

### 4. Role Planning
- **Status**: Observed (6 hosts).
- **Semantics**: `pstack.package.json#/roles` resolved via `scripts/model_role_resolver.py`. Foreign aliases without host catalog match evaluate fail-closed to `BLOCKED`.

### 5. Capability Binding
- **Status**: Observed (6 hosts).
- **Semantics**: 17 typed capabilities mapped in `profiles/<host>.json` conforming to `portability_schema.py`.

### 6. Child Lifecycle
- **Status**: Observed (OMP, Antigravity, Grok).
- **Semantics**: Subagent execution requires explicit start and terminal frames. Progress is private and ephemeral; ended agents leave no live activity.

### 7. Worktree Lease & Hygiene
- **Status**: Observed (all hosts).
- **Semantics**: Isolated worktrees allocated under `.worktrees/<slug>`. Cleanup forces `status.showUntrackedFiles=all` and rejects outside symlinks.

### 8. Policy & Admission
- **Status**: Observed (all hosts).
- **Semantics**: Headless execution cannot bypass human gates. Risky file writes or command executions deny fail-closed without pre-authorization.

### 9. Evidence Receipts
- **Status**: Observed (6 hosts).
- **Semantics**: 4 planes (canonical, adapter, package, runtime). Support states: `packaged`, `configured`, `conforming`. Revision bound to exact git HEAD.

### 10. Review Topology
- **Status**: Observed (Swarm, Arena, Interrogate).
- **Semantics**: Independent seats require distinct model families. Single-family panels report `DEGRADED` diversity.

### 11. Shipping Gate
- **Status**: Observed (all hosts).
- **Semantics**: All functional checks and portable doctor suite must pass. Changes proposed on feature branches and squashed to main.

---

## Consumer Isolation Note
QStack acts strictly as a post-router domain overlay and consumer of PStack's capability descriptors. PStack carries zero reverse dependencies on QStack.
