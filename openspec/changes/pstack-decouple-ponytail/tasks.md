## 1. Tests first

- [ ] 1.1 Replace `test_essential_entries_include_user_ponytail` with a recouple lock: live `01-setup.md`, `HARNESS.md`, and `openspec/specs/pstack-quickstart/spec.md` do not contain `/ponytail`. `plugin.json` still has no ponytail.
- [ ] 1.2 Run the new test and confirm it fails while the docs still name `/ponytail`.

## 2. Docs

- [ ] 2.1 Remove `/ponytail` from `docs/guide/01-setup.md` (Router sentence, after-the-router sentence, Lazy row).
- [ ] 2.2 Remove the HARNESS Skill order YAGNI row that names `/ponytail`.
- [ ] 2.3 Restore `openspec/specs/pstack-quickstart/spec.md` to match the delta.

## 3. Prove

- [ ] 3.1 Re-run `python3 tests/test_verify_harness.py` excluding nested `--log` fetch if the worktree cannot reach upstream.
- [ ] 3.2 `openspec validate pstack-decouple-ponytail --type change --strict`.
