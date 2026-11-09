# PStack upstream semantic boundary: revise epic #916

## Why
PStack is a reference port of official Cursor PStack. The previous Mu/Dogsled proposal tried to specify agent dispatch, worker identity, lifecycle, placement and acceptance as a new PStack domain. Those are execution-platform responsibilities, not PStack semantic responsibilities. Existing OpenSpec capabilities already govern source authority and playbook intent. Keep the useful engineering principles without creating a second platform or a competing specification.

## Change
- Tighten the existing **pstack-reference-port** and **pstack-playbooks** requirements; no new capability name or executable interface.
- Record a short upstream-first semantic crosswalk, with Mu/Dogsled explicitly **reference-only**.
- Preserve upstream orchestrate, swarm, arena and interrogate as *playbook/skill intent*; host adapters implement only their supported bindings.
- Use existing create-verification and create-formal-verification skills for concrete targets, never for hypothetical Mu/Dogsled adapters.
- Record a review/falsification rubric and a three-leaf issue graph for #916.

## Source of authority
- Canonical: [cursor/plugins/pstack](https://github.com/cursor/plugins/tree/main/pstack), classified at the repository's recorded UPSTREAM pin. The earlier research snapshot used cursor/plugins@2776ddd2355d6d6c8747d3964600f28daf62f049; that is an observation, not automatic promotion of the applied pin.
- Local: [tommy-ca/pstack](https://github.com/tommy-ca/pstack); host bindings and conformance evidence are local.
- External references only: [mu-crew/mu@73fb53d](https://github.com/mu-crew/mu/tree/73fb53d4e38c9717be5642460b2344c76cfe6349), [oisin-ee/dogsled@5e28a8c](https://github.com/oisin-ee/dogsled/tree/5e28a8c72272f8d8a91f86c4691a43f4bca6d551).
- Downstream: [tommy-ca/qstack](https://github.com/tommy-ca/qstack); qstack-mode may depend on pstack-mode, never the reverse.

## Non-goals
No agent-orchestration engine, lifecycle protocol, worker store, placement scheduler, queue, external executor adapter, HostExecutionPort, API schema for agent launch, new wiki compiler, model router, or proof of live external execution. No changes to the canonical skill implementations as part of this scope correction.

## Verification status
This change describes specifications and review gates only. OpenSpec CLI, live host execution, independent multi-model Swarm/Arena/Interrogate, and formal model checking must be reported with actual receipts if performed; otherwise NOT_RUN/BLOCKED. Draft PR #930 must be reviewed at its new head; prior CI evidence is not proof for the revision.
