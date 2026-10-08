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
- `tests/test_harness_drivers.py`: driver factory and mocked unavailable-CLI
  behavior; its native CLI smoke cases are explicitly opted out by default.
- `tests/test_project_package.py`: package projections and manifests.
- `tests/test_skill_frontmatter.py`: skill metadata structure.
- `tests/test_scan_host_boundary.py`: host-neutral shared skill boundary.
- `tests/test_package_lifecycle.py`: isolated package lifecycle fixtures.
  
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
