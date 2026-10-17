# Verification test tiers

The test suite has separate **offline contract checks**, **host-dependent CLI
checks**, and **actual observed model-backed runtime proof**. Treat these as
distinct scopes, not interchangeable PASS signals.

## Required pull-request gate (offline)

`.github/workflows/portability-offline.yml` executes Python 3.12/pytest
without installing proprietary agent harness binaries:

- `tests/test_portability_schemas.py`: schema/domain invariants.
- `tests/test_model_role_policy.py`: static model-role policy, pure planner, and fork-index pins. The gate also runs `python -m scripts.model_role_policy` as a checked-in policy preflight.
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
- `tests/test_scaffold_verification_skill.py`: scaffold input validation, ordered feature maps, and the honest non-zero stub.
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
- `tests/test_playbook_parity.py`: playbook contract parity across the shipped
  playbooks and their named hosts.
- `tests/test_review_effect_contracts.py`: the review owners' effect, reachability
  and read-only-audit contracts, with negative controls.
- `tests/test_context_overlays.py`: capability-gated domain overlay packs.
  An overlay loads only when the project declares its capability and the task
  domain matches, and a non-trigger archetype loads no overlay prose at all.
- `tests/test_context_budget_contracts.py`: the measured-context and
  bounded-output owners. It pins the two-owner prose contracts, and validates the
  recorded task-work traces by recomputing their byte components from the
  repository and refuses a gated arm that does more work than its baseline.
- `tests/test_eval_blinded_pstack_dsh_candidate.py`: the candidate phase of the
  #310 E01-E07/N01-N07 corpus. It re-runs the frozen cases on the current tree
  with the controls re-derived in `tests/fixtures/eval_corpus_dsh/candidate_phase.json`
  and asserts that E05 resolves, that no case fails and that every control still
  separates.
- `tests/test_eval_blinded_pstack_dsh.py`: the frozen #310 baseline record. Run it as
  `scripts/eval_blinded_pstack.py --dsh-corpus tests/fixtures/eval_corpus_dsh
  --dsh-phase baseline`. It reports the record as revision-bound drift
  (BLOCKED/UNTESTED history), never a current PASS or FAIL.
- `tests/test_canonical_index.py`: canonical inventory conformance. Its
  classify-drift arm skips as contract BLOCKED when no upstream cache exists;
  the rest runs cache-free.

Two suites in this list are tier-limited and a green job is not a pass for them.
`tests/test_omp_native_package.py` skips without an `omp` binary, so the offline
job proves nothing about native enrollment; that proof would live in an
`observed_live` settlement recorded under `.audit/evidence/` and pinned by a
`profiles/*.json` row. The checked-in durable receipts are static refreshes
(`refresh-static`), so their runtime plane is `UNTESTED` and they prove no live claim.
`tests/test_ci_resource_isolation.py` proves
only its Python half when `node` is absent.
  
A green PR job proves **only these selected contract scenarios**.
`tests/test_package_lifecycle.py` currently does not prove preservation of
unexpected user-authored files inside plugin directories (see `tests/test_package_lifecycle_safety.py`).
None of these checks prove that a real child model was spawned and joined.

## Host-dependent smoke (opt-in)

In `tests/test_harness_drivers.py`, the native CLI discovery/route/spawn-contract/
isolation/receipt cases and the runtime-plane smoke check require:

```sh
PSTACK_RUN_HOST_DEPENDENT_TESTS=1 python -m pytest -q tests/test_harness_drivers.py
```

These checks require locally installed/configured host executables and may fail
without prerequisites. They currently inspect several static/CLI-help surfaces
that **must not be classified as observed live model execution**. A live claim
would rest on an `observed_live` settlement under `.audit/evidence/` plus the
`profiles/*.json` row that pins it; today's durable receipts are static refreshes
and carry runtime `UNTESTED`.

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

The existing four-plane receipt schema remains authoritative for recorded planes.
Never promote historical profile/CLI checks to live evidence.
Historical program #235 (foundation #236/#243, native-proof #238/#248, acceptance #240) is closed. Current program: #429 with sub-epics #430-#433. Current promotion gate: #445.

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

Recorded at `6b0a0e9`, re-verified at the land head, and refreshed statically on
2026-10-17 (receipts bound by surface hash, not commit):

```sh
python scripts/verify-portable.py check-evidence --host all
python scripts/verify-portable.py check-staleness --host all --json
python scripts/verify-portable.py refresh-static --host all
```

The third command is the honest repair for a moved surface: it re-runs the static
doctor planes for each host and records them as that host's durable receipt,
leaving the model-backed runtime plane `UNTESTED`. Its exit status is the doctor
result, so a failing static plane stays `FAIL` instead of riding the `UNTESTED`
overall verdict out as a pass, and a host whose claimed state is `candidate`
(droid) gets no durable receipt written at all.

| Host | Binary on PATH | Durable receipt | Stale planes | Derived support state | Offline verdict |
| --- | --- | --- | --- | --- | --- |
| grok | present | yes (static refresh) | none | packaged | PASS |
| codex | present | yes (static refresh) | none | packaged | PASS |
| omp | present | yes (static refresh) | none | packaged | PASS |
| opencode | present | yes (static refresh) | none | packaged | PASS |
| antigravity | present | yes (static refresh) | none | packaged | PASS |
| droid | present | no (by design) | n/a | candidate | BLOCKED (ineligible host) |

Offline pytest gate on a host with all six binaries present, recorded
2026-10-16: **526 passed, 10 skipped**, plus the one case the static refresh adds
(`tests/test_evidence_durability.py::test_refresh_static_is_partial_and_never_rounds_a_failure_up`).
Every skip is a measured opt-out, never a pass: seven opt-in host CLI
smoke cases in `tests/test_harness_drivers.py`
(`PSTACK_RUN_HOST_DEPENDENT_TESTS=1`), the live model-backed case in
`tests/test_omp_rpc.py`, and the two live-arm cases in
`tests/test_omp_native_package.py` — the last three need
`PSTACK_RUN_OMP_LIVE=1` and a model route. On a host without `node`, `droid` or
the `omp` binary further cases skip instead of passing. Where the upstream cache
is absent (as in CI), the canonical-index classify-drift arm skips instead as
contract BLOCKED.

Every checked-in durable receipt is a static refresh: canonical, adapter and
package `PASS` at the current surface revisions, with runtime and overall
`UNTESTED` and no `observed_live` row. The OMP settlements observed on 2026-10-13
(spawn, cancel, isolation) are historical: the static refresh dropped them because
the runtime surface they proved had moved, and the omp profile now claims
`packaged` with every row `static-only` (and both its ledger claims marked
historical). A live claim comes back only from a live run —
`PSTACK_RUN_OMP_LIVE=1 python3 scripts/verify-portable.py run --host omp`, or
`run --host <host>` where the host CLI and a model route exist — which records a
new `observed_live` settlement for the row that pins it. ### Role modules stay out of the revision inputs (planning-only)

`scripts/model_role_policy.py` and `scripts/model_role_resolver.py` are
deliberately not revision inputs. `plan_role`
(`scripts/model_role_resolver.py:145`) has no production caller — every call
site is in `tests/test_model_role_policy.py`, and the only production
execution of either module is the static CI preflight
(`.github/workflows/portability-offline.yml:54` →
`scripts/model_role_policy.py:225-234`). Both modules consume the
`portability_schema` vocabulary without feeding any revision field, so a stale
copy cannot move a verdict any gate checks. Adding them to `driver_revision`
would force 5 host re-proofs per behaviour edit; adding them to
`package_driver_revision` would fail `check-evidence` at the wrong plane.
Trigger to revisit: the day a recorded scenario depends on either module, name
it in the revision set then. (#473)

A host without a receipt
is `candidate`, never an invented PASS.
