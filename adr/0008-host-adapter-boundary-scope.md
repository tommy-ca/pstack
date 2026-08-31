# Durable host boundaries are adapter-scoped

- Status: Proposed
- Date: 2026-08-31
- Supersedes: ADR-0006

## Context

ADR-0006 correctly established that the Grok pstack playbooks must not create a
second scheduler, database, session manager, or repository-local orchestration
store. Its wording also said that the repository does not ship `scripts/orch`,
but the repository intentionally retains `scripts/orch` and `scripts/watch-pr`
for the Codex compatibility map. The root and `.grok-plugin` manifests are the
Grok pair, while `.codex-plugin` and `.claude-plugin` are separate host adapters
that do not expose Grok-only Benny skills.

## Decision

Keep durable orchestration state host-owned **on the Grok path**:

- Grok playbooks MUST use canonical Grok task and agent state for units, claims,
  frontier, verification, gates, decisions, retries, and fanout/fanin.
- Gas City adapters MUST use Gas City formulas and Beads for durable routing and
  persistence.
- Grok playbooks MUST NOT invoke `scripts/orch/orch.ts`,
  `scripts/watch-pr/watch-pr`, or create a local orchestration store.
- Retained `scripts/orch` and `scripts/watch-pr` files are Codex compatibility
  utilities only and must be labeled as non-Grok surfaces in the Codex map.
- Root and `.grok-plugin/plugin.json` MUST stay in lockstep for the Grok skill
  and agent paths, including Grok Benny skills. Codex and Claude manifests MAY
  expose only their supported shared and host-specific paths and need not expose
  Grok-only Benny skills.

## Consequences

- The Grok safety and durability boundary remains unchanged and is no longer
  contradicted by retained Codex utilities.
- Host adapters can differ without a false global-manifest parity requirement.
- The repository carries compatibility utilities that need their own Codex
  maintenance and tests.
- A future Codex or Claude Benny port requires a separate adapter-specific
  decision and intent change.
