# ADR: Preserve pstack atomic blocks while adapting the host

- **Status:** Accepted (retrospective archive repair)
- **Date:** 2026-08-31

## Decision

Keep the port organized around the upstream pstack atomic blocks: a sticky router, named playbooks, principle skills, host-harness mappings, and optional setup overlays. Translate only host-specific operations to Grok primitives such as `spawn_subagent` and `scheduler_create`; do not copy Cursor-only runtime machinery.

## Rationale

The proposal and tasks identify the block inventory as the shared vocabulary needed for refresh and review. Keeping those boundaries makes each block inspectable and lets the port evolve without coupling source content to a different host runtime.

## Consequences

- Counts and names remain independently verifiable by the harness tests.
- Grok setup may write local role/model overlays rather than modifying upstream source.
- A future upstream refresh must review each block instead of copying host-specific behavior blindly.

## Evidence

This retrospective decision is grounded in the archived proposal, specs, and completed task checklist. It adds no new implementation claim.
