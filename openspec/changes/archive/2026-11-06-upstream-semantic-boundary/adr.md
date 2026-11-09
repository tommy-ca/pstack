# ADR: Keep PStack upstream-semantic, not orchestration-owned

- Status: Proposed (pending review of PR #930)
- Date: 2026-11-06
- Replaces the draft intent of 2026-11-06-agent-orchestration-contracts without changing shipped runtime behavior.

## Decision
1. Official Cursor PStack owns engineering intent: principles, skills, playbooks, ordering, review and verification expectations.
2. This reference port owns accurate semantic preservation/classification and narrowly required host-specific bindings/evidence.
3. A host or an external orchestration product owns processes, lifecycle state, placement, retries, dispatch receipts and resource cleanup *implementation*. PStack does not add contracts for Mu/Dogsled execution.
4. QStack owns quant-specific workflows and may consume PStack semantics by a one-way dependency.
5. Swarm, Arena, Interrogate and Thermos are review methods for this change, not an instruction to ship an orchestration layer.

## Why
SOLID: isolate semantics from execution responsibility. KISS/YAGNI: no speculative adapter or TS execution model. DRY: extend existing OpenSpec capabilities and verification skills rather than duplicate them.

## Alternatives rejected
- Rework the proposed HostExecutionPort and agent lifecycle schema in PStack: rejected, wrong owner and speculative.
- Vendor Mu/Dogsled: rejected, second execution authority and maintenance.
- Remove upstream Orchestrate playbook: rejected, would violate canonical parity.
- Copy runtime contracts into QStack by default: rejected, domain overlay must decide its own implementation and verification.

## Consequences
Delete the old draft change before merge; keep attributed prior-art notes only. Retire #919, #920 and #922 as PStack-scoped work, unless a separate owner later opens them outside this repository. No implementation proof is implied by a design decision.
