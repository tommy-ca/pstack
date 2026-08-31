## 1. Tests first

- [ ] 1.1 Fail then pass: `tests/test_verify_harness.py` asserts `/ponytail` in `docs/guide/01-setup.md` Essential entries, `/ponytail` in `HARNESS.md` Skill order, spec names `/ponytail`, and `plugin.json` has no `ponytail`.
- [ ] 1.2 Run the new asserts and confirm they fail for the missing tokens.

## 2. Docs

- [ ] 2.1 Add Essential entries Kind Lazy: `/ponytail`. After `/poteto-mode`. User plugin. Coding only. Skip if not installed.
- [ ] 2.2 Add HARNESS Skill order row: YAGNI / smallest coding change. Laziness Protocol, then `/ponytail` if inspect lists it, then none.
- [ ] 2.3 Extend `openspec/specs/pstack-quickstart/spec.md` to match the delta.

## 3. Prove

- [ ] 3.1 Re-run `python3 tests/test_verify_harness.py`.
- [ ] 3.2 `openspec validate pstack-essential-ponytail --type change --strict`.
