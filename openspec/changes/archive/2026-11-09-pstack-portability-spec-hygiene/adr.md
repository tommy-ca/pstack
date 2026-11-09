# ADR: Living portability specification hygiene and 1,000-line ceiling enforcement

- Status: Accepted and applied.
- Date: 2026-11-09
- Prior art: Epic #1290 (Pi extension package proof reconciliation).
- Follow-on: Epic #1297 (Portability spec hygiene and ceiling reduction).

## Decisions
1. **Enforce 1,000-line ceiling on living specifications.** In accordance with `/pstack:thermo-nuclear-code-quality-review` Standard 1 and general repository standards, living specifications must remain strictly under 1,000 lines. The living spec `openspec/specs/pstack-portability/spec.md` is compacted from 1,003 lines down to 922 lines by removing redundant whitespace and non-normative narrative repetition.
2. **Strict requirement body length limit.** OpenSpec strict validation flags requirements with bodies exceeding 500 characters as potential anti-patterns (combining multiple behaviors, excessive narrative, or edge cases that belong in scenarios). All 11 requirements in `pstack-portability` exceeding 500 characters are refactored to be <= 500 characters each while preserving 100% of functional requirements and GWT scenarios.
3. **Synchronize static verification evidence in lockstep.** Modifying living specifications changes the SHA-256 digest `spec_hash`. The static evidence receipts across all 6 harnesses in `.audit/evidence/` and `.audit/evidence/index.json` must be refreshed via `python3 scripts/verify_portable.py refresh-static --host all` to avoid staleness failures in CI.
4. **Follow OpenSpec git discipline.** All lifecycle phases cross `main` sequentially: proposal merged before apply, apply merged before archive, and archive executed from `main`.

## Consequences
- `openspec/specs/pstack-portability/spec.md` line count is reduced from 1,003 to 922 lines.
- `bunx @fission-ai/openspec validate pstack-portability --strict` passes with 0 warnings.
- All 6 harnesses maintain fresh static evidence matching the current living specification digest.
