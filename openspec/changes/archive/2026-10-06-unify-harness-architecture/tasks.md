## 1. Intent recording (S1)

- [x] 1.1 Record `unify-harness-architecture` proposal, design, delta scenarios, and ADR manifest for issue #165.
- [x] 1.2 Verify the next free ADR identifier against the occupied `adr/` population (ADR-0001 through ADR-0014 occupied; ADR-0015 used).
- [x] 1.3 Run `openspec validate unify-harness-architecture --type change --strict`.

## 2. Migration (S3)

- [x] 2.1 Absorb the remaining Grok install/sandbox, Herdr, Benny, and forge guidance into `skills/poteto-mode/references/grok-tools.md`, keeping source citations in `docs/guide/13-grok-natives.md`.
- [x] 2.2 Migrate current readers (verification scripts, absorbed checks, tests, scanner documentation, generated manifest description) to the migrated mapping, adopting the reviewed source-dirty hunks.
- [x] 2.3 Update README and translated current instructions for the migrated mapping.

## 3. Retirement and current-state transition (S4)

- [x] 3.1 Remove root `HARNESS.md` after readers migrate; leave archived changes and historical planning records untouched.
- [x] 3.2 Apply this change's deltas to `openspec/specs/` (archive this change) - this is when the new deltas become current; before that, the root file and former paths remain the recorded current state.
- [x] 3.3 Refresh receipts only if hashed inputs changed, and run the applicable gates.
