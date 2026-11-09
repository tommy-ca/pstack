# ADR Review Manifest

- Status: accepted (Epic #906, Unit A #907 fulfilled)
- Review date: 2026-11-06
- Change: 2026-11-06-cross-port-semantic-parity

## In-Force ADRs Reviewed

- `adr/0006-host-owned-orchestration-state.md`: Orchestration state remains host-owned. No foreign state store or child-process engine is imported from comparator.
- `adr/0012-portable-package-descriptor-and-projection.md`: `pstack.package.json` remains canonical authority across the 6-host matrix.
- `adr/0014-portable-verification-skills-architecture.md`: Verification skills stay host-scoped. Negative postconditions are verified directly.
- `adr/0021-harness-neutral-model-role-policy.md`: Model/role configuration resolves against observed host catalogs. Foreign comparator aliases fail closed without unobserved claims.

## Architectural Decision

1. **Clean-Room Negative Invariants**: Borrow failure-oriented postconditions from comparator (`tests/pi/*`, `docs/pi-equivalence.md`) as contract tests in `tests/test_cross_port_contracts.py` rather than importing TypeScript runners or Node child-process runners.
2. **Policy Fork Quarantine**: Declared policy forks in `docs/research/pstack-claude-forks-2026-11-06.json` are maintained as reference comparison data; no policy fork is silently promoted to canonical behavior.
3. **Dual Verification Guardrails**: Maintain strict separation between offline static proof (adapter static checks, contract tests) and observed live host execution.
