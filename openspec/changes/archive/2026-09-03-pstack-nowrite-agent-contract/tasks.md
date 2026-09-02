## 1. Regression contract

- [x] 1.1 Add a pytest that requires `capabilityMode: execute` on the seven no-write agent stems and forbids `capabilityMode` on every other `agents/*.md` file.
- [x] 1.2 Skip `.audit/` in `scripts/verify-harness.py` and `scripts/adapt-harness.py` at any path depth, and ignore `.audit/` in `.gitignore`.
- [x] 1.3 Run the new test and confirm it passes on the current tree.
- [x] 1.4 Name `reflect-judgment` and `reflect-tooling` as prompt posture, not writers.
- [x] 1.5 Assert `.audit` is in both scanners' `SKIP_DIRS`, and that leftover skip matches any-depth `set(rel.parts)`.

## 2. Specification sync

- [x] 2.1 Copy the `pstack-plugin-schema` delta into `openspec/specs/pstack-plugin-schema/spec.md`.
- [x] 2.2 Run `python3 scripts/verify-harness.py`, `uv run --with pytest pytest -q tests/test_verify_harness.py tests/test_release.py`, `grok plugin validate .`, and `openspec validate pstack-nowrite-agent-contract --type change --strict`.
