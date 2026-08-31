## 1. Tests first

- [x] 1.1 Fail then pass. HARNESS names `github-pr-fallback.md` and `gh pr`. The reference maps create/view/checks/merge and forbids `--auto` on non-trunk bases. Playbooks still contain Graphite strings.

## 2. Adapter files

- [x] 2.1 Add `skills/poteto-mode/references/github-pr-fallback.md`. Point the HARNESS Graphite row at it. Do not edit `playbooks/*.md`.

## 3. Prove

- [x] 3.1 `python3 tests/test_verify_harness.py` except nested `--log` fetch if it fails. `openspec validate pstack-github-pr-fallback --type change --strict`.
