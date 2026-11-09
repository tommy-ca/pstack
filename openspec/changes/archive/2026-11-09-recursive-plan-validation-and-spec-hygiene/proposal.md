# Change: Recursive Plan Validation Tooling and Living Specification Hygiene

## Motivation
A deep maintainability and code quality audit under `/pstack:thermo-nuclear-code-quality-review` identified two targeted improvements in recursive plan validation and living specification hygiene:
1. `skills/poteto-mode/scripts/check-plan.mjs` throws an unhandled `ENOENT` error when passed `--help` or `-h` because it attempts to open the flag as a file path instead of displaying CLI usage and exiting with code 0.
2. `openspec/specs/pstack-recursive-plan-validation/spec.md` triggers an OpenSpec 1.16.1 strict validation warning because `Requirement: Multi-phase plans expose a validated dependency graph` exceeds 500 characters (694 characters).

## Proposed Changes
1. Add explicit argument parsing in `skills/poteto-mode/scripts/check-plan.mjs` to intercept `--help` and `-h`, display usage information, and exit with code 0.
2. Add regression tests in `skills/poteto-mode/scripts/check-plan.test.mjs` verifying clean `--help` / `-h` handling.
3. Tighten `Requirement: Multi-phase plans expose a validated dependency graph` in `openspec/specs/pstack-recursive-plan-validation/spec.md` to <= 500 characters (492 characters), distilling non-normative narrative into scenarios and satisfying strict OpenSpec validation without any semantic changes.
4. Verify that `bunx @fission-ai/openspec validate pstack-recursive-plan-validation --strict` passes with 0 warnings.
5. Refresh static evidence receipts across all 6 harnesses.

## Capabilities
### Modified Capabilities
- `pstack-recursive-plan-validation`: Tighten requirement text to <= 500 characters to satisfy strict OpenSpec validation.

## Impact
Zero breaking changes. All scenarios and graph traversal invariants remain fully preserved.
