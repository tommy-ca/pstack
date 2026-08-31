## 1. Spec and tests

- [x] 1.1 Fail then pass `tests/test_release.py` that `plugin.json` version matches `MAJOR.MINOR.PATCH-grokbuild.N` and is not date-only CalVer.
- [x] 1.2 Update live spec, natives Keep row, and ADR 0009.
- [x] 1.3 `openspec validate pstack-semver-not-calver --type change --strict` then archive after merge to main. Do not retag.
