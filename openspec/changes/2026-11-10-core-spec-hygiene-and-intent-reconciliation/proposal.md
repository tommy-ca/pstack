# Change: Reconcile Living Specification Strict Warnings for Intent, Playbooks, and Principles

## Motivation
A deep maintainability and code quality audit under `/pstack:thermo-nuclear-code-quality-review` identified three foundational specifications in `openspec/specs/` that trigger OpenSpec 1.16.1 strict validation warnings because their requirement bodies exceed 500 characters:
1. `openspec/specs/archive-chain-integrity/spec.md`: `Requirement: Archived intent-driven changes retain the full chain` (602 characters).
2. `openspec/specs/pstack-playbooks-not-rhai/spec.md`: `Requirement: Playbooks are not plugin Rhai workflows` (546 characters).
3. `openspec/specs/pstack-principles/spec.md`: `Requirement: Twenty-four principle skills` (512 characters).

## Proposed Changes
1. Compact `Requirement: Archived intent-driven changes retain the full chain` in `openspec/specs/archive-chain-integrity/spec.md` to <= 500 characters by eliminating narrative duplication already covered by scenarios.
2. Compact `Requirement: Playbooks are not plugin Rhai workflows` in `openspec/specs/pstack-playbooks-not-rhai/spec.md` to <= 500 characters.
3. Compact `Requirement: Twenty-four principle skills` in `openspec/specs/pstack-principles/spec.md` to <= 500 characters.
4. Verify all 3 specifications pass `bunx @fission-ai/openspec validate <spec> --strict` with zero warnings.
5. Refresh 6-harness static evidence receipts (`spec_hash` update) and qualify the verification matrix.

## Capabilities
### Modified Capabilities
- `archive-chain-integrity`: Compact requirement description to <= 500 characters to satisfy strict OpenSpec validation.
- `pstack-playbooks-not-rhai`: Compact requirement description to <= 500 characters to satisfy strict OpenSpec validation.
- `pstack-principles`: Compact requirement description to <= 500 characters to satisfy strict OpenSpec validation.

## Impact
Zero breaking changes. All Given-When-Then scenarios, invariants, and assertions remain identical and fully preserved.
