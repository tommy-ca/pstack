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
  real binary. It skips when `omp` is not on PATH, and a skip is not a pass.
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
