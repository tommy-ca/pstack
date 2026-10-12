# Verification test tiers

The test suite has separate **offline contract checks**, **host-dependent CLI
checks**, and **actual observed model-backed runtime proof**. Treat these as
distinct scopes, not interchangeable PASS signals.

## Required pull-request gate (offline)

`.github/workflows/portability-offline.yml` executes Python 3.12/pytest
without installing proprietary agent harness binaries:

- `tests/test_portability_schemas.py`: schema/domain invariants.
- `tests/test_droid_integration.py`: descriptor, profile, lifecycle and
  shape validation. The optional CLI-backed Droid scenarios skip when the
  Droid executable is absent; a skip is **not** a runtime PASS.
- `tests/test_droid_routing.py`: deterministic advisory route regression cases,
  including unknown/partial-match failures.
- `tests/test_route_resolver.py`: pure typed route resolution and precedence.
- `tests/test_verdict_reduction.py`: failure-first verdict lattice and timeouts.
- `tests/test_harness_drivers.py`: driver factory and mocked unavailable-CLI
  behavior; its native CLI smoke cases are explicitly opted out by default.
- `tests/test_project_package.py`: package projections and manifests.
- `tests/test_skill_frontmatter.py`: skill metadata structure.
- `tests/test_scan_host_boundary.py`: host-neutral shared skill boundary.
- `tests/test_package_lifecycle.py`: isolated package lifecycle fixtures.
- `tests/test_package_lifecycle_safety.py`: unmanaged file and symlink safety.
- `tests/test_evidence_durability.py`: durable evidence/plane staleness.
- `tests/test_select_checks.py`: change-scoped selection table and exact-head
  evidence binding.
- `tests/test_sync_antigravity_plugin.py`: the sync source guard (dirty tree,
  linked worktree, non-repository, and the `--force` override).
- `tests/test_omp_native_package.py`: the OMP native package proof against the
  real binary. It skips when `omp` is not on PATH, and a skip is not a pass. Its
  vertical-slice half (#292) keeps an ungated offline arm — package projection,
  manifest shape, uninstall plan and the four-plane receipt with a BLOCKED
  runtime plane — so the job still runs something real without a binary.
- `tests/test_ci_resource_isolation.py`: concurrent-process resource isolation,
  with the colliding fixture as the negative control. The Node half skips when
  `node` is absent.
- `tests/test_evidence_receipts.py`: check-evidence receipt binding.
- `tests/test_omp_rpc.py`: the RPC reducer and its offline frames. Its live case
  is gated by `PSTACK_RUN_OMP_LIVE=1`.

Two suites in this list are tier-limited and a green job is not a pass for them.
`tests/test_omp_native_package.py` skips without an `omp` binary, so the offline
job proves nothing about native enrollment; that proof lives in the live tier
tracked by issues #238 and #240. `tests/test_ci_resource_isolation.py` proves
only its Python half when `node` is absent.
  
A green PR job proves **only these selected contract scenarios**.
`tests/test_package_lifecycle.py` currently does not prove preservation of
unexpected user-authored files inside plugin directories (see #239/#249).
None of these checks prove that a real child model was spawned and joined.

## Host-dependent smoke (opt-in)

In `tests/test_harness_drivers.py`, the native CLI discovery/route/spawn-contract/
isolation/receipt cases and the runtime-plane smoke check require:

```sh
PSTACK_RUN_HOST_DEPENDENT_TESTS=1 python -m pytest -q tests/test_harness_drivers.py
```

These checks require locally installed/configured host executables and may fail
without prerequisites. They currently inspect several static/CLI-help surfaces
that **must not be classified as observed live model execution**. See #238/#247.

The broader `tests/test_verify_portable.py` integration tests invoke OpenSpec,
harness doctors and other external tools; they are **not** part of the minimal
offline PR job until the relevant dependencies and proof semantics are isolated.
Other repository tests not listed in the offline gate remain unassessed by that
gate. A full suite pass from a prepared developer machine is not a substitute
for explicit isolated runtime receipts.

## Change-scoped selection (which gate a patch actually needs)

Running the whole matrix for a docs edit wastes the tiers. Select the minimal gate
that can fail for the changed paths:

```sh
python scripts/verify-portable.py select-checks --base <base-ref> [--head <sha>] [--json]
```

It resolves the real merge base, collects the changed paths (`git diff --name-only`
against the merge base, plus staged/unstaged/untracked context when the head is
`HEAD`), and maps them through one table of path pattern → checks. The table draws
only on the tiers above: the offline contract modules (read out of
`.github/workflows/portability-offline.yml`, never re-listed), the other
`tests/*.py` modules, and the standalone verifier scripts. Each planned check is
labelled `offline` (in the PR gate), `host_dependent` (needs the documented
opt-in), or `outside_gate` (not proven by the PR gate — run it, but a skip is not
a pass). A path with no mapping defaults to the full offline set and is reported
as unmapped; selection never silently returns nothing.

The plan is a *selection*, not a new verdict source: the forge's own check state
stays authoritative, and `fix-ci`/`babysit` own the loop that consumes the plan.

### Exact-head evidence binding

A selection result is bound to the head SHA and the `git patch-id` of the
merge-base..head diff:

```sh
python scripts/verify-portable.py select-checks --base <base-ref> --record <path> \
  --outcome 'pytest:tests/test_x.py=PASS'
python scripts/verify-portable.py select-checks --base <base-ref> --receipt <path>
```

Retargeting, rebasing onto a changed base, or reworking the patch changes the
patch-id, which invalidates the receipt: its `FAIL`/`BLOCKED`/`PASS` may not be
quoted as current CI. A pure rebase keeps the patch-id, so the recorded verdict
still describes the patch and only mergeability and the checks at the new head
need re-running. This is the same patch-id rule the shipping playbooks use.

## Acceptance matrix (not yet complete)

- Offline conformance: PR CI job and exact commit SHA.
- Live host preflight: binary path, version, environment and bounded exit code.
- Observed runtime: actual safe route/spawn/join/cancel where native host APIs
  permit; record exact commands, child outcome, cleaned workspace, and evidence.
- Ineligible host: explicitly `UNTESTED` or `BLOCKED`, never invented PASS.
- Candidate Droid: do not infer model-backed runtime support from contract tests.

The existing four-plane receipt schema remains authoritative for recorded planes,
but its current runtime PASS semantics are being corrected in #238/#247/#248.
Never promote historical profile/CLI checks to live evidence during migration.

Program: #235. Foundation #236/#243. Native-proof work #238/#248. Acceptance #240.

## Adversarial acceptance and the six-host matrix (#294)

P8 attacks the shipped artefacts and asserts the refusal instead of assuming the
guardrails hold. Each negative lives beside the machinery it attacks, inside the
offline gate above:

| Attack | Guardrail exercised |
| --- | --- |
| Fake wire alias (a real host primitive declared as the `task` wire) | `tests/test_verdict_reduction.py::test_fake_wire_alias_fails_the_native_subagent_contract` (OMP + OpenCode, honest-alias control), `::test_a_missing_wire_alias_never_passes_by_default` |
| An alias meant to legitimize a host primitive in a shared skill | `tests/test_verdict_reduction.py::test_an_aliased_host_primitive_stays_forbidden_in_shared_surfaces` |
| A shadowed `poteto-mode` / duplicate route row | `tests/test_verdict_reduction.py::test_shadowed_poteto_mode_never_wins_the_canonical_route` |
| An invented verdict token | `tests/test_verdict_reduction.py::test_an_invented_verdict_token_never_reduces_to_pass` |
| A child defect masked as a missing model route | `tests/test_verdict_reduction.py::test_a_missing_model_route_is_blocked_while_a_child_defect_is_not_masked` |
| An ambient-defined agent credited to the package | `tests/test_verdict_reduction.py::test_an_ambient_defined_agent_is_flagged_so_the_package_cannot_claim_it` |
| A session pickup standing in for a child resume | `tests/test_evidence_durability.py::test_a_session_pickup_never_satisfies_a_child_resume_pin` |
| A cancelled / timed-out / errored child settlement | `tests/test_evidence_durability.py::test_a_non_success_child_settlement_never_satisfies_a_verified_pin` |
| A `verified` pin naming an unrecorded scenario | `tests/test_evidence_durability.py::test_a_verified_pin_naming_an_unrecorded_scenario_is_a_dangling_reference` |

Attacks refused by a suite this unit does not own, with where the refusal lives:

- WorkPool reviewer contamination and a cancelled lane reported as a pass:
  `tests/test_playbook_parity.py`. There is **no executable freshness API** — the
  gate is the prose contract `eval.workpool.freshAgents=true` observed in the
  run's effective settings, locked by that suite. Treat it as a contract gate, not
  runtime enforcement.
- Unapproved apply/merge: `tests/test_swarm_apply.py` (dry-run refuses a fenced
  copy and writes nothing) and `tests/test_swarm_partition.py` (`apply_check`
  raises `SystemExit(2)` on a leftover/fence/missing destination).
- Stale receipts: the staleness cases in `tests/test_evidence_durability.py` plus
  the patch-id binding in `tests/test_select_checks.py`.
- Cleanup and data loss: `tests/test_worktree_cleanup.py` (WIP worktrees classify
  as hold buckets) and `tests/test_package_lifecycle_safety.py` (unmanaged user
  files survive every lifecycle step). `PortableVerifier.cleanup` is a no-op, so
  it cannot lose evidence.
- Timeout / cancel: `tests/test_omp_rpc.py` reducer cases plus the bounded
  `run_command` timeout in `tests/test_verdict_reduction.py`.

### Six-host offline matrix

Recorded at the P8 head `716bca5` with no receipts rewritten:

```sh
python scripts/verify-portable.py check-evidence --host all
python scripts/verify-portable.py check-staleness --host all --json
```

| Host | Binary on PATH | Durable receipt | Stale planes | Derived support state | Offline verdict |
| --- | --- | --- | --- | --- | --- |
| grok | present | yes | none | supported | PASS |
| codex | present | yes | none | supported | PASS |
| omp | present | yes | none | packaged | PASS |
| opencode | present | yes | none | supported | PASS |
| antigravity | present | yes | none | supported | PASS |
| droid | present | no (by design) | n/a | candidate | BLOCKED (ineligible host) |

Offline pytest gate at that head: **381 passed, 10 skipped**. The skips are the
tier-limited cases, never passes: `tests/test_omp_native_package.py` (needs the
`omp` binary and, for the live arm, `PSTACK_RUN_OMP_LIVE=1` with a model route),
the Node half of `tests/test_ci_resource_isolation.py`, the opt-in host CLI smoke
in `tests/test_harness_drivers.py`, and the optional CLI-backed Droid scenarios.

The model-backed live tier was **not** executed and no receipt was regenerated,
so the runtime plane stays `UNTESTED` for every host in this record; OMP's derived
state remains `packaged` for exactly that reason. A host without a receipt is
`candidate`, never an invented PASS.
