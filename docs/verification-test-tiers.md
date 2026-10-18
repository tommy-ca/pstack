# Verification test tiers

The test suite has separate **offline contract checks**, **host-dependent CLI
checks**, and **actual observed model-backed runtime proof**. Treat these as
distinct scopes, not interchangeable PASS signals.

## Required pull-request gate (offline)

`.github/workflows/portability-offline.yml` executes Python 3.12/pytest
without installing proprietary agent harness binaries:

- `tests/test_portability_schemas.py`: schema/domain invariants.
- `tests/test_host_identity.py`: the host identity seam (#446) — one module owns
  the closed six and the namespaced rule a declared host id must satisfy, the four
  host-bearing schemas reference that one definition, and a declared host stays
  candidate/GAP while a collision, an unknown name and an unattributed receipt all
  fail closed.
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
`profiles/*.json` row. Four of the five checked-in durable receipts are static
refreshes (`refresh-static`), so their runtime plane is `UNTESTED` and they prove
no live claim. The omp receipt is the exception: it was written by the supported
run path (`PSTACK_RUN_OMP_LIVE=1 python3 scripts/verify-portable.py run --host omp`,
run `omp-1792295156-c0f6f0a9`), so its runtime plane is a live `PASS` and the four
rows those settlements cover (`agent.spawn`, `agent.join`, `agent.cancel`,
`workspace.isolated`) are `verified` pins into it.
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
`profiles/*.json` row that pins it; the static-refresh durable receipts carry
runtime `UNTESTED`, and only the omp receipt's live run carries the settlements
named above.

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

Recorded at `6b0a0e9`, re-verified at the land head, refreshed statically on
2026-10-17, and omp re-observed live on 2026-10-18 (receipts bound by surface
hash, not commit):

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
(droid) gets no durable receipt written at all. For a host that has live rows it
keeps the runtime rows but drops the settlements they carried, so the runtime
plane re-reduces to `UNTESTED` and the profile rows that pin those settlements
fail the scenario-pin gate instead of passing silently; restoring them takes the
live run path (`PSTACK_RUN_OMP_LIVE=1 ... run --host omp`).

| Host | Binary on PATH | Durable receipt | Stale planes | Derived support state | Offline verdict |
| --- | --- | --- | --- | --- | --- |
| grok | present | yes (static refresh) | none | packaged | PASS |
| codex | present | yes (static refresh) | none | packaged | PASS |
| omp | present | yes (live run `omp-1792295156-c0f6f0a9`) | none | packaged | PASS |
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

Four of the five checked-in durable receipts are static refreshes: canonical,
adapter and package `PASS` at the current surface revisions, with runtime and
overall `UNTESTED` and no `observed_live` row. The omp receipt is the live
exception — run `omp-1792295156-c0f6f0a9` records the runtime plane `PASS` with
three `observed_live` settlements (spawn, cancel, isolation), which is what the
omp profile now pins: `agent.spawn` and `agent.join` into `runtime-child-spawn-omp`,
`agent.cancel` into its capability-scoped cancelled settlement on
`runtime-child-cancel-omp`, and `workspace.isolated` into `runtime-isolation-omp`.
Those four rows are `verified`; every other row stays `static-only` or `unverified`,
so the profile still claims `packaged` and its ledger records the promotion. The
2026-10-13 settlements the 2026-10-17 static refresh had dropped are restored, not
remembered. A live claim comes back only from a live run —
`PSTACK_RUN_OMP_LIVE=1 python3 scripts/verify-portable.py run --host omp`, or
`run --host <host>` where the host CLI and a model route exist — which records a
new `observed_live` settlement for the row that pins it. A host without a receipt
is `candidate`, never an invented PASS.

### Claim freshness planes are cumulative, and the inventory is read too

`check-evidence` gates a level claim on the planes that level rests on, and the
planes accumulate: `packaged` proves the package plane, `verified` keeps it and
adds canonical, adapter and runtime, `supported` keeps all four across every row.
`verified` used to check only the behavioral three, so a stale package driver —
`scripts/package-lifecycle.py`, `pstack.package.json` or the plugin manifest —
failed the `packaged` claim one rung below and passed the `verified` claim above
it. Pinned by
`tests/test_evidence_durability.py::test_a_verified_claim_evaluates_the_package_plane`
and, for the level below,
`::test_stale_package_driver_rejected_for_packaged_claim`. (#473)

The same command reads `.audit/evidence/index.json` as evidence, not only as a
cache: every row is compared with the receipt it names on `run_id`, `timestamp`,
`planes` and `surface_revisions`, and a host with a durable receipt but **no row**
reports `STALE/REBUILD-REQUIRED` naming the receipt, because deleting a row was
the F4 remedy that used to pass silently. Rebuild with
`python3 scripts/verify-portable.py refresh-static --host <host>` — unless the
orphan receipt cannot be read at all (that failure reports a repair, since a run
refuses to rewrite bytes it cannot read) or the host claims `candidate` (which
writes no durable receipt, so the orphan is removed instead). A host with
neither row nor durable receipt (droid) has nothing to inventory and keeps
reporting `NOT_COVERED`. Pinned by
`tests/test_evidence_durability.py::test_a_row_less_host_with_a_durable_receipt_reports_rebuild_required`
and `::test_check_evidence_fails_when_a_row_disagrees_with_its_receipt`. (#495)

### What a receipt does not bind (recorded gap)

A durable receipt binds the host binary (`host_version`) and the recorded surface
revisions. It does **not** bind the host's model catalog or the pstack
schema/harness-catalog hash, so a `verified` receipt proves the surfaces and
binary it names and never the model catalog a live route would resolve. The
receipt schema states this in its own description
(`schemas/portability/receipt.schema.json`). Closing it means new
`VerificationReceipt` fields plus a restamp of all five durable receipts and the
index, which is out of scope for this unit; the gap is recorded here rather than
implied by the word `verified`. (#444)

The external `qstack` quant-domain overlay is pinned as a **post-routing**
boundary: `tests/fixtures/qstack-overlay-routing.json` declares the contract
(stage `post-routing`, owns no router or model namespace) and the overlay's
activation table, and
`tests/test_context_overlays.py::test_qstack_overlay_stays_post_routing_and_leaves_routes_unchanged`
binds the production half: the route each of the six harnesses resolves for one
fixed need (`TDD` → `/tdd`), and the assertion that no file under `scripts/` or
`profiles/` mentions qstack at all, so wiring the overlay into pstack routing or
into a profile's model namespace reddens there. The declared contract and
activation table are checked against this repo's overlay-gating semantics
(`select_overlays` in that module), not by executing the external pack: they pin
the declaration, and profile drift is what reddens the route half. (#444)

### Role inputs join the package revision (planner code, policy, schema)

`plan_role` (`scripts/model_role_resolver.py:151`) has exactly one production caller —
`project-package.py --check` → `check_model_role_plan`, a read-only per-host planning
probe — plus the call sites in `tests/test_model_role_policy.py`, and that is still the
whole set (`tests/test_model_role_policy.py::test_plan_role_has_exactly_one_production_caller`
re-derives it from `scripts/`). The only other production execution of the policy module
is the static CI preflight (`.github/workflows/portability-offline.yml:54` →
`scripts/model_role_policy.py:256-258`). Because that probe builds its verdict from the
policy bytes, the schema that validates them, and the planner code that interprets them,
all four join `package_driver_revision`: the two planner modules by behaviour-bearing AST
core, the policy and the schema byte for byte. A probe-verdict change from any of the four
fails a `packaged` claim closed on the package plane instead of passing silently. The
schema is read with raw bytes (no AST could carry a tightening enum), and a deleted policy
or schema moves the digest to a value no receipt carries, so both deletions fail closed.
Measured before the fix: the mutated policy left `check-evidence` and `check-staleness`
both exiting 0; proven 2026-10-19, neutralising `unproven_catalog_reason` flips the grok
probe DEGRADED → PLANNED with the policy untouched, so code-only coverage was required too.
Pinned by `test_mutated_model_role_policy_stales_the_package_plane` (policy edit, policy
deletion, schema deletion) and `test_mutated_planner_module_stales_the_package_plane`
(resolver behaviour edit). `portability_schema.py` itself stays in `driver_revision` (its
constants feed the adapter plane via validation), and the probe modules stay out of
`driver_revision`, so a planner behaviour edit costs one package-plane re-proof, not five
host re-proofs. (#473)
