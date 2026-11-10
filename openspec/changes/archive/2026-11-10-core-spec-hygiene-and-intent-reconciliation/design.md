# Design: Reconcile Living Specification Strict Warnings for Intent, Playbooks, and Principles

## Context
Foundational specifications for archive chain integrity, playbook routing, and principles define normative contracts across PStack. OpenSpec 1.16.1 flags requirement descriptions exceeding 500 characters with strict warnings.

## Architecture & Code Judo Decisions
1. **Archive Chain Integrity**: In `openspec/specs/archive-chain-integrity/spec.md`, streamline the requirement body to 462 characters. Scenarios `Complete archived chains pass`, `Missing historical artifacts fail closed`, `Historical content is not rewritten`, and `External work stays visibly deferred` specify detailed edge cases and outcome annotations.
2. **Playbooks Not Rhai**: In `openspec/specs/pstack-playbooks-not-rhai/spec.md`, streamline the requirement body to 459 characters (including `Feature:` line), removing repetitive prose regarding discovery paths covered in scenarios.
3. **Principles Inventory**: In `openspec/specs/pstack-principles/spec.md`, streamline the requirement body to 350 characters (including `Feature:` line).
4. **Zero Invariant Drift**: No scenario, tag, test assertion, or interface contract is modified.
