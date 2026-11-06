# Source-grounded deep audit, caller map and upstream semantic crosswalk

Audit baseline: `tommy-ca/pstack` `main@b356beff9c6d75b7a9cf28940c1209462e2a1b09`; original PR #958 base `100230addcceb34583f80b3cf796e6e86dbbd619`. The main branch advanced across package lifecycle, Antigravity package proof, sync, verification-scaffolding and verification skill docs; no implementation PR may overwrite these updates. Reconcile branch base before shipping.

## Source authority matrix
| Source | Observation | Authority |
| --- | --- | --- |
| [Cursor `setup-pstack` @ applied `88d47514`](https://github.com/cursor/plugins/blob/88d47514b82e7c44f00f2b2a72ff6dd12158038c/pstack/skills/setup-pstack/SKILL.md) | eight steps including both optional ordinary and **formal** verification skill creation | **Canonical applied intent** |
| [Cursor `setup-pstack` @ observed `2776ddd`](https://github.com/cursor/plugins/blob/2776ddd2355d6d6c8747d3964600f28daf62f049/pstack/skills/setup-pstack/SKILL.md) | one changed sentence about Arena cross-judge family selection; no automatic pin upgrade | candidate upstream freshness |
| [Port `setup-pstack`](https://github.com/tommy-ca/pstack/tree/main/skills/setup-pstack) | neutral entry today dispatches via `SetupProjection.skill` | current port implementation, **not** new semantic authority |
| [Port `setup-pstack-grok`](https://github.com/tommy-ca/pstack/tree/main/skills/setup-pstack-grok) | complete Grok-native probe/ask/validate/write/confirm, only *ordinary* verification offer | host adapter prior art, preserve behavior except upstream parity delta |
| [Port `setup-projection.schema.json`](https://github.com/tommy-ca/pstack/blob/main/schemas/portability/setup-projection.schema.json) | currently has optional `skill`, `source`, `effort`, `catalog`, `overlay` | one current typed wire/schema owner |
| [Port `SetupProjection`](https://github.com/tommy-ca/pstack/blob/main/scripts/portability_types.py) | `SETUP_SHAPES` requires `skill` for host-cli and currently enforces semantic shapes | one typed runtime model |
| [Port `resolve_setup_projection`](https://github.com/tommy-ca/pstack/blob/main/scripts/setup_pstack.py) | exact declared `host` lookup, currently checks skill file existence | one resolver to simplify |
| [Port `model_role_resolver`](https://github.com/tommy-ca/pstack/blob/main/scripts/model_role_resolver.py) | already owns override precedence and static evidence tier | do not duplicate |
| [QStack `qstack-mode`](https://github.com/tommy-ca/qstack/tree/main/skills/qstack-mode) | consumes independently installed PStack `poteto-mode` | downstream only, no reverse dependency |

## Applied Cursor principles -> concrete decisions
- [Subtract Before You Add](https://github.com/cursor/plugins/blob/88d47514b82e7c44f00f2b2a72ff6dd12158038c/pstack/skills/principle-subtract-before-you-add/SKILL.md): omit speculative `SetupProjection.reference` field; delete existing Grok public skill after migrating callers.
- [Migrate Callers Then Delete Legacy APIs](https://github.com/cursor/plugins/blob/88d47514b82e7c44f00f2b2a72ff6dd12158038c/pstack/skills/principle-migrate-callers-then-delete-legacy-apis/SKILL.md): remove `SetupProjection.skill`, references, tests and manifest entries together; do not ship dual dispatch. Actual external compatibility requires documented release/rollback proof.
- [Boundary Discipline](https://github.com/cursor/plugins/blob/88d47514b82e7c44f00f2b2a72ff6dd12158038c/pstack/skills/principle-boundary-discipline/SKILL.md) and [Type System Discipline](https://github.com/cursor/plugins/blob/88d47514b82e7c44f00f2b2a72ff6dd12158038c/pstack/skills/principle-type-system-discipline/SKILL.md): exact host identity and file confinement checked once at profile boundary, no untyped alias.
- [Make Operations Idempotent](https://github.com/cursor/plugins/blob/88d47514b82e7c44f00f2b2a72ff6dd12158038c/pstack/skills/principle-make-operations-idempotent/SKILL.md): repeat setup writes safely, preserve unrelated user files and atomically stage generated root mirror.
- [Prove It Works](https://github.com/cursor/plugins/blob/88d47514b82e7c44f00f2b2a72ff6dd12158038c/pstack/skills/principle-prove-it-works/SKILL.md): direct host observation vs offline smoke, and exact SHA receipts.
- [QStack Declare Your Falsifier](https://github.com/tommy-ca/qstack/tree/main/skills/qstack-principle-declare-your-falsifier): a *testing method* for negative controls only, not a PStack quant dependency.
- [Thermo Nuclear Review](https://github.com/cursor/plugins/tree/main/thermos/skills/thermo-nuclear-review) reviews changed-diff correctness and regressions; [Thermo Nuclear Code Quality Review](https://github.com/cursor/plugins/tree/main/thermos/skills/thermo-nuclear-code-quality-review) challenges indirection, duplicate state and complexity; neither is asserted to have run as an independent agent.

## Profiles: explicit current setup-key inventory (nine files)
| file | host | setup mode | `skill` currently present? | migration |
| --- | --- | --- | --- | --- |
| antigravity.json | antigravity | host-catalog | **null** | remove key; retain catalog |
| claude.json | claude | absent/candidate | no | retain GAP |
| codex.json | codex | host-catalog | **null** | remove key; retain catalog |
| copilot.json | github:copilot | absent/candidate | no | retain GAP |
| droid.json | droid | inherit/candidate | **null** | remove key |
| grok.json | grok | host-cli | **setup-pstack-grok** | remove key; reference now derived as `grok.md` |
| omp.json | omp | none | **null** | remove key |
| opencode.json | opencode | none | **null** | remove key |
| pstack-pi.json | pstack:pi | inherit/candidate | no | preserve |

**P0:** six packaged profiles carry `skill`, including five that store `null`. Schema removal must migrate **six packaged and six root mirror copies**, not only `grok.json`. Current root+packaged copies were byte-identical when audited; do not infer that a future checkout remains so.

## Concrete current call sites to migrate
Current default-branch code search finds operational references in:
- `skills/setup-pstack/SKILL.md`, `skills/setup-pstack-grok/SKILL.md`, Grok references `defaults.toml`, `effort-ladder.md`, `resolve-model.md`, `resolve-effort.md`, and both sets of `skills/setup-pstack/profiles/*.json` and `profiles/*.json`.
- `scripts/setup_pstack.py`, `scripts/portability_types.py`, `schemas/portability/setup-projection.schema.json`, `scripts/adapt_harness.py`, `scripts/package_projection.py` (these call `resolve_setup_projection` and depend on catalog/execution split).
- `scripts/verify_harness.py` has multiple **hardcoded** `setup-pstack-grok/references/*` paths, requires `setup-pstack-grok/SKILL.md` and checks its "use one of"/effort claims; move assertions to the native `grok.md` reference with unchanged Grok-only safety expectations.
- `scripts/scan_host_boundary.py` explicitly exempts `skills/setup-pstack-grok/**` and `skills/setup-pstack/profiles/**`; remove the retired skill exemption but keep only a bounded native-reference/profile exemption. The neutral `setup-pstack/SKILL.md` must remain scanned for host-specific leakage.
- `scripts/package_lifecycle.py`, `scripts/prove_antigravity_native_package.py`, `scripts/sync_antigravity_plugin.py` require both canonical packaged profiles and root distribution; newer `main` changed them after PR #958 base. Their behavior must be preserved, not overwritten by a stale branch.
- `scripts/drivers/base.py`, `scripts/surface_revisions.py`, `scripts/evidence_index.py`, `scripts/scaffold_verification_skill.py`, `scripts/verify_pi_candidate.py`, `scripts/eval_decision_routing.py` and `scripts/verify_rollback_equivalence.py` use `resolve_profiles_dir`; verify migration when changing canonical preference.
- `tests/test_setup_projection.py` currently asserts `skill="setup-pstack-grok"`, legacy dispatch directory existence and that shared entry names `skills/<setup.skill>/SKILL.md`; change all to strict convention resolution and no legacy field.
- `tests/test_harness_profiles_sync.py` calls the packaged location `CANONICAL_PROFILES` but tests root-first `resolve_profiles_dir()`; update to canonical-first with explicit parity negative test. Current test also duplicates two invocation blocks; a cleanup can remove redundant calls in the same test.
- `tests/test_verify_harness.py`, `tests/test_scan_host_boundary.py`, `TEST-PLAN.md`, `README.md`, `README.zh-CN.md`, host-native Grok tool refs and current operational skill links in `swarm`, `arena`, `interrogate`, `how`, `why`, `architect`, `poteto-mode` need a caller sweep.
- Older `docs/audit/thermo-nuclear-695` is historical source evidence; DO NOT rewrite history as if the old skill never existed. Operational instructions must not advertise it after migration.

This is an indexed source audit; repository-wide searches and exact package depgraph should be rerun on the implementation branch before marking #949 complete. Filesystem clones may include generated files absent from GitHub code search.

## Risk ledger
| Severity | Finding | Impact / accepted remedy |
| --- | --- | --- |
| P0 | Existing living setup spec requires dispatch to second skill | use MODIFIED requirements, not only ADDED requirements |
| P0 | Six host setup profiles have the legacy `skill` key | remove from all six source profiles + mirrors atomically with strict schema |
| P1 | Proposed `reference` would be a redundant pointer | derive matching reference by validated profile filename |
| P1 | Upstream includes formal verification offer; Grok has only ordinary offer | preserve both as explicitly optional, non-duplicating follow-up actions |
| P1 | Canonical packaged location but root-first resolver | canonical-first + parity; no immediate deletion of root |
| P1 | Current main diverged from PR branch in package/verification code | merge/rebase latest main before code delivery and re-run tests |
| P1 | Existing Grok setup write-only note vs optional verify skill creation | separate setup mutation from explicitly requested skill-generation follow-up |
| P1 | Model alias `inherit-parent` vs effort alias on Grok differ | document frontmatter effort fallback, do not claim direct parent-effort inheritance |
| P2 | Stale operational refs to second setup skill/old profile paths | exhaustive consumer/package scanner gate prior to deletion |
| P2 | `host-catalog` is projection, not runtime setup | no false native-write claims |
