# Design: Recursive Plan Validation Tooling and Living Specification Hygiene

## Context
The recursive plan validation specification defines machine-readable plan section identifiers and cycle detection enforced by `check-plan.mjs`.

## Architecture & Code Judo Decisions
1. **CLI Flag Dispatch**: In `skills/poteto-mode/scripts/check-plan.mjs`, check `process.argv.slice(2)` for `--help` or `-h`. If present, print usage text to stdout and exit cleanly with code 0 before any file I/O occurs.
2. **Spec Hygiene & Compaction**: In `openspec/specs/pstack-recursive-plan-validation/spec.md`, tighten `Requirement: Multi-phase plans expose a validated dependency graph` to 492 characters by removing repetitive phrasing while keeping normative constraints intact.
3. **Zero Invariant Drift**: All existing scenarios (`independent and nested tasks validate`, `unknown dependency fails closed`, `duplicate identifiers fail closed`, `dependency cycle fails closed`) remain identical.
