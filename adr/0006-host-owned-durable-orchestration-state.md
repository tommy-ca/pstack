# Durable orchestration state stays host-owned

- Status: accepted
- Date: 2026-08-31

## Context

The pstack Grok playbook coordinates long-running work, but the port does not ship the `scripts/orch` command or a durable local orchestration store. Gas City methodology packs already route work, retries, persistence, and fanout/fanin through formulas, drains, expansions, and Beads. A playbook-local scheduler or database would create a competing source of truth.

## Decision

PStack playbooks MUST keep durable orchestration state in the host's canonical task and agent state. The playbooks MUST NOT create a second scheduler, database, session manager, or repository-local orchestration store. Gas City adapters use Gas City formulas and Beads for durable units, claims, frontier state, verification, gates, decisions, retries, and fanout/fanin. If a host lacks a field, the coordinator records a gate or reported gap instead of adding a parallel store.

## Consequences

The orchestrate playbook remains host-neutral and does not prescribe a local CLI or file layout. Host adapters must map its conceptual records to their existing durable APIs. This avoids duplicate state and keeps recovery, retries, and liveness in the host graph, at the cost of requiring an explicit gate when a host cannot represent a needed field.
