## 1. Lock adapter policy

- [x] 1.1 Add focused manifest tests covering root/`.grok-plugin` parity and intentional Codex/Claude omission of Grok-only Benny skills.
- [x] 1.2 Add a harness-doc assertion that retained `scripts/orch` and `scripts/watch-pr` utilities are labeled non-Grok compatibility surfaces.

## 2. Reconcile durable decisions

- [x] 2.1 Add the superseding ADR-0008 without editing accepted ADR-0006.
- [x] 2.2 Update the durable `pstack-grok-host-boundary` spec wording and scenario names to scope host-owned state and parity to Grok while documenting adapter asymmetry.
- [x] 2.3 Update the live host mapping text to match the new ADR and spec without changing Grok playbook behavior.

## 3. Verify and hand off

- [x] 3.1 Run `python3 scripts/verify-harness.py`, `uv run --with pytest pytest -q tests/test_verify_harness.py`, and `grok plugin validate .`.
- [x] 3.2 Run `openspec validate clarify-pstack-host-adapter-boundaries --type change --strict` and preserve the result before archive eligibility.
- [x] 3.3 Recheck that Grok playbooks still have no local watcher/store path and that no plugin-global hooks were added.
