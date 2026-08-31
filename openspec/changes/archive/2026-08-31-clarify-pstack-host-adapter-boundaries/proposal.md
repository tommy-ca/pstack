## Why

The Grok host-boundary correction is behaviorally right, but ADR-0006 still says
that the repository does not ship `scripts/orch` even though the retained Codex
adapter deliberately maps those utilities. The adapter manifests are also
intentionally asymmetric, yet the durable scenario title implies every host
manifest must expose Grok-only Benny skills. Clarifying both boundaries prevents
future reviewers from treating intentional host separation as drift.

## What Changes

- Scope host-owned durable orchestration language explicitly to the Grok path.
- Document retained `scripts/orch` and `scripts/watch-pr` utilities as Codex
  adapter surfaces, not Grok runtime state managers.
- Clarify that root and `.grok-plugin` manifests are the Grok parity pair, while
  `.codex-plugin` and `.claude-plugin` may omit Grok-only Benny skills.
- Add regression assertions for the intentional manifest asymmetry and ADR
  wording.
- Align the user-facing verification guide with the host-owned `monitor` boundary and cover the wording with a regression assertion.
- Do not delete retained host-specific utilities or change live Grok behavior.

## Capabilities

### New Capabilities

- `pstack-host-adapter-boundaries`: Define the separation between Grok, Codex,
  and Claude adapter surfaces and their durable-state ownership.

### Modified Capabilities

- `pstack-grok-host-boundary`: Narrow durable-state and manifest-parity wording
  to the host surfaces where it applies.

## Impact

Affected files are `adr/0006-host-owned-durable-orchestration-state.md`, the
PStack Grok host-boundary durable spec, host-adapter documentation, the
verification guide, and `tests/test_verify_harness.py`. No runtime dependency,
plugin hook, provider, workflow, or publication surface changes.
