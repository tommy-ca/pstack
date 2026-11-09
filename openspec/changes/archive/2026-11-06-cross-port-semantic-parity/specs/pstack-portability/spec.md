# pstack-portability: three-source cross-port parity contract

## ADDED Requirements

### Requirement: Three-source cross-port comparisons bind canonical and comparator pins

Every three-source semantic audit MUST record exact commit SHAs and licensing provenance for canonical Cursor PStack, reference comparator `pstack-claude`, and target `tommy-ca/pstack`. Declared comparator policy forks (`tools/forks.json`) MUST be explicitly classified into `adapt`, `preserve`, `exclude`, or `policy-fork`. No policy fork MAY be promoted to canonical without formal acceptance.

#### Scenario: Comparator policy fork is triaged
- **GIVEN** a declared fork in comparator `tools/forks.json`
- **WHEN** evaluated against canonical intent and target host requirements
- **THEN** it is classified in `docs/research/pstack-claude-forks-2026-11-06.json`
- **AND** comparator-specific policy modifications are not applied as canonical behavior

### Requirement: Failure-oriented negative postconditions are verifiable across hosts

Contract verifiers MUST enforce negative failure postconditions:
1. Canceled or terminated children must fail closed and never report PASS.
2. Tool completion must correlate with exact invocation ID.
3. Worktree cleanup must fail safe when untracked or uncommitted files exist.
4. Authorization requests without explicit grant must deny.
5. Canceled timers must not deliver late wakeups.

#### Scenario: Headless permission request without explicit grant
- **GIVEN** a headless execution context requiring human permission
- **WHEN** no interactive terminal or pre-authorized rule exists
- **THEN** the request denies fail-closed
- **AND** no execution proceeds
