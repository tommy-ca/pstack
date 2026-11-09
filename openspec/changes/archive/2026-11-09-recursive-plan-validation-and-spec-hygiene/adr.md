# ADR-0022: Tighten Recursive Plan Validation Requirement and Support CLI Help Flags

## Status
Accepted

## Context
OpenSpec 1.16.1 flags requirement descriptions longer than 500 characters with strict warnings. Concurrently, `check-plan.mjs` lacked clean `--help` handling.

## Decision
1. Tighten `Requirement: Multi-phase plans expose a validated dependency graph` to 492 characters.
2. Add `--help` / `-h` support to `check-plan.mjs` exiting 0 with usage instructions.

## Consequences
- Strict OpenSpec validation passes with 0 warnings on `pstack-recursive-plan-validation`.
- CLI usability is improved and prevents spurious `ENOENT` stack traces.
