## Why

The canonical Cursor pstack 0.15.21 intent is already ported into `tommy-ca/pstack` with typed capability bindings, six declared hosts, deterministic package projection and evidence receipts. `michael-denyer/pstack-claude` demonstrates additional executable ports (Claude Code hooks, Codex/Copilot routing, a Pi extension), generator-enforced role/model consistency, and mechanism-level equivalence tests. Today the target has a `claude` enum but no `profiles/claude.json`, no `copilot` host enum, and no single validated model/role resolution contract. Cross-repo pattern transfer must not accidentally import another port's policy forks, orchestration store, or runtime-only claims.

## What Changes

- Introduce a **proposal-stage**, typed model/role policy schema with stable role IDs, selection topology, host-local catalogs, provider/family identity, effort and fallback.
- Define deterministic authority/precedence, runtime catalog detection, safety/approval constraints, independence requirements, observable resolution receipts, and no-phantom-model rules.
- Adopt `pstack-claude`'s one-source generator and runtime-equivalence *patterns*, not its host-specific implementation wholesale.
- Specify portable routing-hook lifecycle, opt-out and no-double-injection gate; keep existing host-owned orchestration state.
- Produce an auditable parity matrix and a fail-closed implementation graph with Swarm, Arena, Interrogate and real-runtime proof gates.
- Preserve `qstack` as an external domain overlay, never an alternate host router.

## Modified capabilities

- `pstack-portability`: model/role resolution, package hooks, freshness, evidence and host support gates.

## Non-goals

No new workflow engine, scheduler, database, provider proxy, code copy of the entire Pi extension, new agent model vendor, or unsupported claim of runtime parity. This change is design-only until implementation tasks pass.
