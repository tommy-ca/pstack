# Implementation plan — epic #1164

## 1. Source baseline and compatibility (#1167)

- [x] 1.1 Audit existing `openspec/config.yaml`, vendored schema, 5 templates, active/archive boundaries and immutable ADR-0007/0019/0020.
- [x] 1.2 Compare against [intent-driven-template](https://github.com/intent-driven-dev/intent-driven-template), pin template source and reject wholesale OpenCode/agent/toolchain replacement.
- [ ] 1.3 Inspect all active and archived chains and record missing/skip_specs anomalies without rewriting historical artifacts.

## 2. Intent inspection CLI (#1165)

- [x] 2.1 Add a source-only, ordered five-stage artifact inspector to existing `scripts/openspec_change.py` with `--status --json --change`.
- [x] 2.2 Add strict separate `verify` that checks artifact completeness, the schema and actual CLI validation, failing closed when binary missing.
- [x] 2.3 Add missing, symlink, traversal, docs-only, multi-change and no-CLI unit tests to existing `tests/test_openspec_change.py`.
- [ ] 2.4 Run new tests on exact PR head and inspect status JSON for all active changes.

## 3. Operator entrypoints and verification (#1166)

- [x] 3.1 Add `openspec:status` and `verify:openspec` tasks to existing `mise.toml`.
- [x] 3.2 Extend `tests/test_runtime_toolchain.py` and offline workflow to assert both tasks and test inspector behavior.
- [ ] 3.3 Run `openspec schema validate intent-driven` and `openspec validate <selected-change> --type change --strict` on a prepared host; unavailable CLI means NOT_RUN/BLOCKED.

## 4. Documentation, review and release gate (#1167, #1168)

- [x] 4.1 Update `docs/verification-test-tiers.md` to distinguish filesystem status, strict OpenSpec validation, native harness runtime, and independent multi-agent reviewer outputs.
- [x] 4.2 Reconcile PStack `openspec/config.yaml` with non-destructive host-neutral template guidance; preserve applied upstream semantics and six host adapters.
- [ ] 4.3 Run exact-head offline PR CI, syntax, existing check-plan, six-harness doctor (preflight and actual effects classified distinctly).
- [ ] 4.4 Execute independent Swarm/Arena/Interrogate and both Thermos review skills on the actual changed diff; record models, reviewers and output, or NOT_RUN.
- [ ] 4.5 Update epic #1164 and child issue evidence, synchronize living requirements, then archive only after strict OpenSpec validation and accepted merge.
