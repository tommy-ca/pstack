# ADR: exclude DeepSeek-specific skill implementations; reuse PStack owners

**Date:** 2026-11-07  
**Status:** PROPOSED (specification only; no merged runtime change).  
**Scope:** source-ledger refresh and `pstack-reusable-skill-patterns`.

## Context
DeepSeek Harness includes 22 agent skills at the inspected source commit, including DSH architecture and Cordis plugin lifecycle, macOS signing, native GitHub stack semantics, branding, and session projections. An earlier PStack audit of 16 source skills already established host-neutral source-to-owner mapping. Copying DSH skill names would duplicate PStack functionality and import unwanted host/product dependencies.

## Decision
Retain a **22-row historical source census** but let only **12 general** and **5 task-conditional general** behavioral patterns be candidates for PStack reuse. **Exclude five DSH-specific source skills as independent PStack capabilities**. Map every retained behavior to one existing PStack leaf skill, a principle and a playbook. Add no new installed skill, principle, playbook, router, adapter, evidence enum or runtime package in this change. A new artifact requires a later demonstrated unique invocation/output gap.

## Rationale
- **SOLID:** PStack's current leaf/host/evidence owners remain independent of upstream DSH concepts.
- **KISS/DRY:** preserve one copy of each rule, write only the smallest missing contract.
- **YAGNI:** features tied to one OS, product, external merge interface or event-store implementation stay outside common PStack.
- **Trust:** source prose is lower-trust documentation, not approval to mutate systems or credentials.
- **Dependency:** QStack overlays PStack in one direction, never vice versa.

## Alternatives rejected
- Vendor all 22 SKILL.md directories or register a `dsh-*` namespace.
- Add a new generic router or orchestration engine.
- Make Cordis, projection persistence, `gh stack`, signed CUA, bilingual documents, DSH PR template, SVG sizes or GUI GIF mandatory across projects.
- Rewrite historical 16-source evidence as though it described today's 22-source snapshot.

## Consequences
PStack's current skills remain unchanged; remaining implementation proposals require source-behavior diffs against exact PStack owners, targeted negative controls, independent review when actually run, exact-head verification and honest host-by-host receipts. Other domain projects may reuse a generic invariant through their own project verifier without inheriting the DSH-specific skill.
