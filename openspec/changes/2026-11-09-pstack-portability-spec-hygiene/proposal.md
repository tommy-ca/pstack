# Change: Reconcile 1,000-line ceiling and strict validation in living portability specification

## Motivation
A deep maintainability audit under `/pstack:thermo-nuclear-code-quality-review` revealed two code-health issues in the living specification `openspec/specs/pstack-portability/spec.md`:
1. File size reached 1,003 lines, violating the 1,000-line ceiling standard.
2. Direct strict validation `bunx @fission-ai/openspec validate pstack-portability --strict` exited with 11 warnings due to requirement descriptions exceeding 500 characters.

## Proposed Changes
1. Compact and tighten the 11 long requirements in `openspec/specs/pstack-portability/spec.md` so that each requirement description is <= 500 characters, moving non-normative narrative and redundant prose into concise scenario assertions.
2. Remove excessive whitespace and repetitive clauses, reducing total line count from 1,003 lines to <= 900 lines while preserving 100% of functional requirements, bindings, and GWT scenarios.
3. Refresh 6-harness static evidence receipts with the new `spec_hash`.

## Capabilities
### Modified Capabilities
- `pstack-portability`: Tighten requirement texts to pass strict OpenSpec validation and enforce the 1,000-line ceiling.

## Impact
Zero breaking changes. All 31 requirements, 54 GWT scenarios, data models, and conformance floors remain fully intact and semantically equivalent.
