# ADR-0023: Compact Core Living Specification Requirements for Strict OpenSpec Validation

## Status
Accepted

## Context
OpenSpec 1.16.1 flags requirement descriptions exceeding 500 characters under strict validation. Three core specifications (`archive-chain-integrity`, `pstack-playbooks-not-rhai`, and `pstack-principles`) exceeded this threshold due to non-normative narrative in requirement headers.

## Decision
1. Compact the requirement descriptions of all three specifications to <= 500 characters while preserving all existing Given-When-Then scenarios and semantic invariants.
2. Verify with `bunx @fission-ai/openspec validate --changes --strict` and `validate <spec> --strict`.

## Consequences
- Strict OpenSpec validation passes with zero warnings across all three foundational specifications.
- Specification readability is enhanced under `principle-minimize-reader-load`.
- Eliminates narrative bloat under `principle-subtract-before-you-add`.
