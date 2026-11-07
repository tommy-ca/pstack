# ADR: DeepSeek 22-skill refresh uses existing PStack owners

**Date:** 2026-11-07  
**Status:** PROPOSED — documentation-only, not runtime adoption.  
**Scope:** `pstack-reusable-skill-patterns` and its existing source lineage.

## Context
PStack previously source-pinned 16 DeepSeek Harness skills. The inspected upstream commit now contains 22 directories, including host-specific additions. PStack already owns generic review, verification, documentation, orchestration and host adapters. A new skill namespace or framework would duplicate these owners.

## Decision
Keep `poteto-mode` and its existing playbooks, owner skills, host adapters, and evidence reducer. Extend the existing OpenSpec capability and source crosswalk; make extra lifecycle, session, UI, PR and host-specific guidance **conditional**, with negative triggers and executable proof requirements. Refrain from copying DSH instructions or scripts.

## Consequences
- 22 entries must have revision/path, decision and canonical owner.
- 8 changed existing sources require a behavior-level re-review, not automatic source-prompt synchronization.
- GitHub stacks, macOS signing, model-backed browser recordings, DSH styling and documentation pairing remain project/host-specific.
- Swarm, Arena and Interrogate can evaluate proposed adaptations, but this spec revision does **not** claim their execution.
- The original archived source materials and closed epic #305 remain historically true.
- Implementation is separate, reversible and bound by existing authorization and verification rules.

## Rejected
Wholesale vendor import, a common `dsh-*` router, a new evidence status vocabulary, and a generalized event-sourcing engine for all development tasks.
