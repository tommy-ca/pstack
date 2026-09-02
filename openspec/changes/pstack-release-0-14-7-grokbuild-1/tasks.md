## 1. Audit the unreleased range

- [x] 1.1 Record that `v0.14.7-grokbuild.0` stays at `420f4ec` and `HEAD` is six signed commits ahead.
- [x] 1.2 Record that `481091d` bundled tests for three concerns and that history will not be rewritten.

## 2. Specs and manifests

- [x] 2.1 Merge the increment-N requirement into durable `openspec/specs/pstack-release-tag/spec.md`.
- [x] 2.2 Set the six tracked version surfaces and the `UPSTREAM` this-port line to `0.14.7-grokbuild.1`.
- [x] 2.3 Run `python3 scripts/verify-harness.py` and `uv run --with pytest pytest -q tests/test_verify_harness.py tests/test_release.py`.
- [x] 2.4 Run `openspec validate pstack-release-0-14-7-grokbuild-1 --type change --strict`.

## 3. Land on main

- [ ] 3.1 Commit OpenSpec artifacts, then the version bump, as signed Conventional Commits.
- [ ] 3.2 Push `main` to origin without `--force`.

## 4. Tag and Release

- [ ] 4.1 From a host shell run `./scripts/release.sh`.
- [ ] 4.2 Confirm origin has `v0.14.7-grokbuild.1`, GitHub has that Release, and `v0.14.7-grokbuild.0` still points at `420f4ec`.
