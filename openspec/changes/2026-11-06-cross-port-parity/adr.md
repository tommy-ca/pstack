# ADR Review Manifest: Cross-Port Parity

- Status: accepted (Epic #906, Units A-E fulfilled)
- Review date: 2026-11-06
- Change: 2026-11-06-cross-port-parity

## In-Force ADRs Reviewed

- `adr/0006-host-owned-orchestration-state.md`: Orchestration state remains host-owned; no external state store or child-process engine is imported.
- `adr/0012-portable-package-descriptor-and-projection.md`: `pstack.package.json` remains canonical authority across the 6-host matrix.
- `adr/0014-portable-verification-skills-architecture.md`: Verification skills stay host-scoped. Negative postconditions are verified directly.
- `adr/0021-harness-neutral-model-role-policy.md`: Model/role configuration resolves against observed host catalogs.

## Architectural Decision

Clean-room adoption of observable negative contracts in `tests/test_cross_port_contracts.py` and bounded formal invariant falsification in `scripts/verify_cross_port_invariants.py`, while curating source-attributed semantic atoms in `.llm-wiki/`. All 65 declared comparator forks classified.
