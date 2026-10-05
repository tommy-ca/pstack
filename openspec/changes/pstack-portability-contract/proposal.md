## Why

The current port has strong Grok-specific implementation evidence, but cross-harness portability is split across Grok call-site mappings, Codex/Claude notes, hardcoded inventories, and host-specific verification. This change makes the portability boundary explicit without adding a workflow runtime.

## What Changes

- Add a consolidated `pstack-portability` OpenSpec capability.
- Make official `cursor/plugins/pstack@UPSTREAM` the only canonical authority.
- Classify this repository as a reference port with Grok as the strongest current reference adapter.
- Define harness lifecycle states: candidate, mapped, packaged, verified, supported.
- Preserve `swarm`, `arena`, and `interrogate` as composed pstack skills.
- Formalize lever verification from Build the Lever, Prove It Works, and create-verification-skill.
- Separate canonical, adapter, and runtime conformance.
- Replace normative hardcoded principle and playbook counts with discovery from the pinned canonical tree.
- Update the porting guide around the same contract.

## Capabilities

### New Capabilities

- `pstack-portability`: Formalizes the minimal portable capability surface, adapter binding model, and three-plane conformance.

### Modified Capabilities

- None.

## Impact

Affects `docs/guide/12-porting.md`, `openspec/specs/pstack-portability/spec.md`, `openspec/specs/pstack-principles/spec.md`, and `openspec/specs/pstack-reference-port/spec.md`. No runtime engine or workflow DSL is introduced.
