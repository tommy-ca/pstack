## Why

The Grok port still carries two host-boundary leaks from earlier drafts: babysitting names a repository-local watcher that is not shipped, and orchestration prescribes a second `scripts/orch` state store instead of using the host's durable task graph. The optional Benny guard also allows a compound local merge followed by a plain push, while the adapter manifest omits the live Benny skill path. Fixing these now keeps the port executable and prevents safety and state drift from spreading into future playbooks.

## What Changes

- Replace the missing `scripts/watch-pr/watch-pr` babysit path with the documented Grok `monitor` primitive and forbid playbook-local polling.
- Remove the nonexistent `scripts/orch/orch.ts` store and define the durable-state boundary: host canonical task/agent state owns units, claims, frontier, verification, gates, and decisions; Gas City adapters use Gas City formulas and Beads.
- Extend the optional Benny fail-closed guard to deny a compound local merge followed by a plain push while retaining prompt-enforced Slack policy and non-global hook scope.
- Keep the root and `.grok-plugin` manifests aligned for version, skill paths, and agent path, including the live Benny skill tree.

## Capabilities

### New Capabilities

- `pstack-grok-host-boundary`: Host-native monitoring, canonical durable orchestration state, and lockstep adapter metadata for the Grok port.

### Modified Capabilities

- `benny-grok-remap`: Extend the optional fail-closed guard contract to cover compound local merge-and-push commands without making it a plugin-global hook.

## Impact

- `skills/poteto-mode/playbooks/babysit.md` and `orchestrate.md` change operational instructions only.
- `automations/benny-grok/bin/fail-closed.sh`, `plugin.json`, and `.grok-plugin/plugin.json` change the optional safety and packaging contracts.
- `tests/test_verify_harness.py` gains regression checks for the missing paths, guard escape, and manifest drift.
- A new repository ADR records that durable orchestration state remains host-owned; no new dependency or runtime service is introduced.
