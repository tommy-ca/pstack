## 1. Regression guard

- [x] 1.1 Add a fixture-backed test for checked, unchecked, and archived change directories.
- [x] 1.2 Run the fixture test red before implementing the guard.

## 2. Durable spec cleanup

- [x] 2.1 Replace generated Purpose placeholders in the twelve affected durable specs.
- [x] 2.2 Implement the active task-complete design/ADR guard in `verify-harness.py`.

## 3. Verification

- [x] 3.1 Run the scanner, direct harness test script, and focused pytest smoke.
- [x] 3.2 Run focused pytest for the guard and Purpose contract.
- [x] 3.3 Run `openspec validate pstack-spec-hygiene --type change --strict` before archive.
