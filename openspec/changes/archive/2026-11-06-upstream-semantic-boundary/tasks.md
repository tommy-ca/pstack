# Recursive issue graph — upstream semantic boundary (#916)

This change retains only PStack-owned specification work. All checkboxes are honest work statuses, not claims of executed validation.

~~~text
#916 PStack upstream semantics scope (epic)
  #917 Source inventory / external-reference dispositions
    -> #918 Existing-capability OpenSpec requirements + design
      -> #921 Review/acceptance evidence: Swarm, Arena, Interrogate, Thermos
        -> #930 Draft PR validation and independent review
~~~

## Kept, re-scoped
- [x] #917: inventory and classify canonical vs Mu/Dogsled source references (source-only; no runtime tests).
- [x] #918: draft revised requirements, ADR, code/data/documentation flow and minimal attribution record.
- [x] #918: validate OpenSpec with available CLI, reconcile against the existing pstack-reference-port/pstack-playbooks specs.
- [x] #921: perform actual independently sourced review only when capable; record all non-runs.
- [x] #921: review the final diff under both Thermos lenses; reject duplicated capability and speculative architecture.
- [x] #930: re-run relevant offline checks and inspect fresh head-SHA CI, then accept or revise.

## Retired as PStack work
- #919: Mu/Dogsled child-agent lifecycle verification belongs to actual executor owners; generic skills already exist.
- #920: Mu/Dogsled optional executor adapter is explicitly out of scope.
- #922: QStack-specific orchestration/wiki adoption is a downstream owner decision, not a PStack implementation task.

## Definition of done
- Only current PStack capabilities receive spec deltas; no new runtime types or adapter code.
- Every source-derived claim has an owner/disposition and immutable reference.
- Any missing executable, independent reviewer or checker is NOT_RUN/BLOCKED.
- Issues and PR cross-reference this graph, with no duplicate runtime epics in PStack.
- The revision is reviewed against the exact PR head; old CI receipts are not reused as current proofs.
