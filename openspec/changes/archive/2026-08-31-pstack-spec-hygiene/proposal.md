## Why

Twelve durable PStack specs still carry generated `TBD` Purpose text, so the repository's contract index does not explain what those specs own. The OpenSpec CLI also accepts historical archived changes that lack `design.md` or `adr.md`; a small pre-archive guard can protect future intent chains without rewriting those historical records.

## What Changes

- Replace generated `TBD` Purpose text with concise, evidence-backed descriptions in the twelve affected durable specs.
- Add a read-only harness guard that checks active, task-complete changes for `design.md` and `adr.md` before they can be treated as archivable.
- Add fixture-backed regression coverage for complete versus incomplete changes and preserve archived historical directories unchanged.
- Record the pre-archive intent-chain gate as a durable workflow decision.

## Capabilities

### New Capabilities

- `pstack-intent-hygiene`: Prevent task-complete active changes from reaching archive without design and ADR artifacts.

### Modified Capabilities

None. Purpose text is clarified without changing existing requirement behavior.

## Impact

- Twelve files under `openspec/specs/` receive Purpose-only updates: Grok host/natives/workflows, harness map/markdown, playbooks, plugin schema, principles, reference port, router, setup overlays, and upstream sync.
- `scripts/verify-harness.py` and `tests/test_verify_harness.py` gain the guard and its fixture-backed check.
- A new top-level ADR records the enforcement boundary; no runtime dependency, archive rewrite, or historical artifact repair is introduced.
