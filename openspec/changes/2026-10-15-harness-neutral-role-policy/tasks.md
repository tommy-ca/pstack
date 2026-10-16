# Recursive implementation plan

This branch formalizes the proposed interface; it does not assert production implementation.

- [ ] **G0** Approve canonical/reference parity and explicit policy-fork classification; check frozen commits and licenses.
- [ ] **G1** Accept Arena architecture seam, Interrogate review of the formal change, and unique-role model with schema fixtures.
- [ ] **G2** Implement deterministic role/model/effort resolver with model discovery, precedence, fail-closed negative paths and receipt identity.
- [ ] **G3** Integrate projector/model roles and host-local hooks; preserve installed files and opt-out; do not overwrite user configuration.
- [ ] **G4** Add Claude Code native profile/manifest and limited runtime smoke; classify supported capabilities honestly.
- [ ] **G5** Add Copilot candidate/profile only after source/license and host capability analysis.
- [ ] **G6** Run Pi-vs-OMP *separate* parity and capability checks; do not copy another host's process/session manager.
- [ ] **G7** Run Swarm host matrix, Arena design comparison and independent Interrogate review on exact implementation head.
- [ ] **G8** Run strict OpenSpec, schema, projection, role fixture and host-native acceptance tests with durable receipts, then apply/archive accepted requirements.

Dependency graph:

```mermaid
flowchart LR
  G0[Provenance & inventory] --> G1[Formal schema acceptance]
  G1 --> G2[Resolver & catalog]
  G2 --> G3[Projection and hooks]
  G1 --> G3b[Host identity registry #446]
  G2 --> G3b
  G2 --> G4[Claude runtime]
  G3 --> G4
  G2 --> G5[Copilot candidate]
  G3 --> G5
  G3b --> G5
  G0 --> G6[Pi/OMP parity]
  G2 --> G6
  G4 --> G7[Swarm/Arena/Interrogate]
  G5 --> G7
  G6 --> G7
  G7 --> G8[Proof and archive]
```

Every child issue MUST state its dependency, deterministic acceptance, file/API ownership and evidence type. Parent closes only when all dependent tasks are proven or explicitly descoped with reason.

## Published GitHub execution graph (2026-10-15)

Program: [#429](https://github.com/tommy-ca/pstack/issues/429). Draft spec: [PR #428](https://github.com/tommy-ca/pstack/pull/428).

| Epic | Children | Dependencies |
| --- | --- | --- |
| [#430](https://github.com/tommy-ca/pstack/issues/430) Provenance/spec | #434, #435, #436 | #434 → #435 → #436 |
| [#431](https://github.com/tommy-ca/pstack/issues/431) Role/model | #437, #438, #439 | #436 → #437 → (#438, #439) |
| [#432](https://github.com/tommy-ca/pstack/issues/432) Adapters | #440, #441, #442, #443, #446 | #437/#438 → #440 → (#439 →) #441; #434/#437 → #443; #436/#437 → #446; #440/#446 → #442 |
| [#433](https://github.com/tommy-ca/pstack/issues/433) Verification | #444, #445 | #435/#437/#440/#441/#442/#443 → #444; #436/#438/#439/#444 → #445 |

These are **open issues** until their acceptance criteria receive independent evidence. The source review is not a completed live multi-model Swarm/Arena/Interrogate run.

## Design-to-code progress snapshot (2026-10-15, PR #428)

The policy schema now supports bounded `seats` independent of distinct model slugs. The draft includes `scripts/model_role_resolver.py`, a pure role-planning seam with explicit precedence, declared capability gaps, cross-judge selection, and honest status labels. No native harness is dispatched. All host-specific model/provider calls remain future tasks #440–#444. Issue #437 stays open until actual host integration and runtime receipts settle.

The planner output now has a JSON Schema Draft 2020-12 wire contract (`schemas/portability/model-plan.schema.json`); tests check both honest error plans and rejection of forged runtime PASS. This is a **static type contract**, not a live host integration or settlement protocol.

## New design task #446 (P1) — extensible host identity

Parent: #432. Dependencies: #436 and #437. Implement a bounded, backwards-compatible declarative host identity registry following the formal OpenSpec requirement, with unique namespaced IDs and fail-closed capability states. No host is added automatically by the static model-role policy. Future Copilot issue #442 MUST consider this contract before extending the closed enums; do not duplicate host inventory sources. PR #428 documents the contract; #446 performs code migration only after acceptance.
