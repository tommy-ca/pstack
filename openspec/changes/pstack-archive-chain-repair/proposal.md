## Why

Four completed OpenSpec archive entries have checked task lists but no `design.md` or `adr.md`, so archive validation reports completion without preserving the intent-driven artifact chain. This makes historical decisions impossible to review consistently and weakens the repository's own lifecycle contract.

## What Changes

- Add concise retroactive design and ADR-review artifacts to the four affected archives: `pstack-atomic-blocks`, `pstack-grok-host-contract`, `pstack-sync-from-upstream`, and `pstack-plugin-schema`.
- Add a repository regression check that every archived change contains proposal, specs, design, ADR, tasks, and metadata artifacts.
- Preserve archived proposals, specs, task wording, implementation history, and existing durable specs unchanged.

## Capabilities

### New Capabilities

- `archive-chain-integrity`: Archived intent-driven changes retain their complete planning chain.

### Modified Capabilities

- `pstack-verification-harness`: Archive integrity is checked alongside existing OpenSpec and runtime contract checks.

## Impact

- Documentation-only repair under `openspec/changes/archive/` plus one static test in `tests/test_verify_harness.py`.
- No product/runtime behavior changes and no new dependency.
- The repair is retrospective; it does not rewrite historical self-references or claim that these artifacts existed at their original implementation time.
