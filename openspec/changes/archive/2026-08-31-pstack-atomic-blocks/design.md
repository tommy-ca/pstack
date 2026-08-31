## Context

Retrospective artifact for the archived `pstack-atomic-blocks` change. Its proposal, specs, tasks, and implementation history are present, but the design handoff was omitted before archival. The change describes the official Cursor pstack block inventory and its Grok host remap.

## Goals / Non-Goals

**Goals:**

- Preserve the implemented decomposition into router, playbooks, principles, harness map, and setup overlays.
- Record the source/runtime boundary and the provider-call translations that the existing tasks and tests describe.
- Make the archive's intent chain complete without rewriting historical content.

**Non-Goals:**

- No new runtime behavior.
- No Cursor `make-bot-ui` copy, Benny wiring, or new planning runtime.
- No claim that the retrospective design existed before the original implementation.

## Decisions

1. The router selects one of the 22 named playbooks and preserves the `opening-a-pr` terminal step.
2. The 21 principle skills remain individually addressable and are indexed by the router.
3. Cursor `Task` is represented by the Grok `spawn_subagent` contract, and recurring `/loop` work maps to `scheduler_create`.
4. `/setup-pstack` owns optional model/effort overlays under the Grok home directory.
5. Official source material is reference input; harness-specific behavior is adapted outside the source boundary.

## Verification

The archived tasks record the official-versus-port inventory, OpenSpec strict validation, parent-owned mapping review, and independent count checks. This file is a retrospective summary of those existing claims, not additional execution evidence.
