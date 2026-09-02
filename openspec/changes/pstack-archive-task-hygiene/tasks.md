## 1. Close external task outcomes truthfully

- [ ] 1.1 Amend task 3.3 in `openspec/changes/archive/2026-08-31-pstack-release-actions-proof/tasks.md` with the original marketplace action, `Outcome: deferred`, its unavailable evidence reason, and the sibling-repository follow-up.
- [ ] 1.2 Amend task 3.3 in `openspec/changes/archive/2026-08-31-pstack-release-tag-host-push/tasks.md` with the original conditional marketplace action, `Outcome: deferred`, its unavailable evidence reason, and the sibling-repository follow-up.
- [ ] 1.3 Sync the modified `archive-chain-integrity` requirement and preserve the original archive proposals, specifications, designs, ADRs, and task intent.

## 2. Verify archive hygiene

- [ ] 2.1 Run `openspec validate --archived --strict` and confirm neither release archive reports an unchecked task.
- [ ] 2.2 Run `python3 scripts/verify-harness.py`, `python3 tests/test_verify_harness.py`, and `python3 tests/test_release.py`.
- [ ] 2.3 Confirm the sibling `grok-build-plugins` checkout and installed host state were not mutated by this change.
- [ ] 2.4 Run `openspec validate pstack-archive-task-hygiene --type change --strict` and review the final diff for false execution claims.
