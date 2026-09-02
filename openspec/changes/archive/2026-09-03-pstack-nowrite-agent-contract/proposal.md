## Why

Grok 1.0.13 takes `capabilityMode` from agent YAML, not from spawn. `execute` means read plus shell and no file edits. Specs and tests pin that field on `how-explorer` and `independent-verifier` only. The other no-write roles can lose it without a red gate. A verifier or explorer that silently gains write tools breaks the grok-native split this port exists to preserve.

## What Changes

- Name a closed set of no-write plugin agents that MUST ship `capabilityMode: execute`.
- Name that writers, `why-*`, and `reflect-*` MUST NOT ship `capabilityMode`, so a writer cannot lose file edits by copy-paste and those roles stay prompt posture.
- Add a pytest that fails if either side of that set drifts.
- Keep `scripts/verify-harness.py` and `scripts/adapt-harness.py` from scanning `.audit/` at any path depth so local decision trails cannot trip Cursor leftover gates.
- Sync the `pstack-plugin-schema` delta into the durable spec.
- Do not change spawn names, effort ladder, inheritSkills, host install, archive, release, or playbook text except where a test comment would lie.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `pstack-plugin-schema`: require a closed no-write agent set to carry `capabilityMode: execute`, and require every other plugin agent to omit that field.

## Impact

`agents/*.md` (asserted, not rewritten unless a member is already wrong), `tests/test_verify_harness.py`, `openspec/specs/pstack-plugin-schema/spec.md`, and this change's planning artifacts. No host plugin update. No new dependency.
