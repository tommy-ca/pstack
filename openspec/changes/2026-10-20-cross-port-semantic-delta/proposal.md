## Why

Program #429 closed the initial harness-neutral role/model and pstack-claude parity effort. Since its comparator snapshot (`94f5ce95`), `michael-denyer/pstack-claude` advanced 16 commits to `88f6d39f` (0.9.95). Target `tommy-ca/pstack` completed canonical 0.15.29 pin synchronization under Program #622 (closed via #630/#643 on main `329acf2`), while maintaining six native host targets (Grok, Codex, OMP, OpenCode, Antigravity, Droid). The comparator pstack-claude delta remains an independent cross-port delta requiring source-pinned classification and negative-test validation without creating runtime forks.

## What Changes

- Define a **three-source semantic delta**: (canonical, reference-port, target-port), pinned by commit SHA and classified by behavioral contract, owner and evidence rather than filename or blob diff.
- Refine the reusable **atomic blocks** for intent routing, policy principles, playbook composition, model/role choice, capability projection, task lifecycle, durable state, worktree safety, evidence reduction, and review topology.
- Reuse the comparator's updated Pi activity, process and cleanup **negative-test scenarios** where they express host-neutral postconditions. Preserve separate host-native implementations, including OMP's task/RPC mechanisms.
- Specify reversible gates for promotion; use the already-open #622 upstream synchronization and #630 exact-head acceptance, not a second release router or proof ledger.
- Keep accepted runtime-dependent changes behind adapter/profile boundaries, and classify policy forks explicitly.

## Modified capabilities

- `pstack-portability`: source provenance, host-scoped lifecycle evidence, semantic fanout, and failure-aware worktree conformance.

## Non-goals

No automatic upstream pin bump; no copied Claude/Pi implementation, process manager or new orchestrator; no seventh declared host by implication; no invented model IDs or multi-model execution; no automatic merge, destructive cleanup, or duplicate qstack router. This PR is **design/documentation only**. Runtime changes require their own reviewed implementation PR and actual host receipts.
