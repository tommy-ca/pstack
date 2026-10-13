# ADR 0020: Skip-Specs Exception to Post-Archive Completeness

- Status: accepted
- Date: 2026-10-13

## Context

ADR-0019 decision 1 requires every directory under `openspec/changes/archive/` to contain at least one `specs/**/*.md` delta, via `scripts/verify-harness.py::archived_changes_missing_artifacts()`. Some archived changes are docs-only plan carriers: they reconcile plans, decisions, or cited evidence and intentionally introduce no behavioral delta, so they carry no spec delta by design and were being failed by that check.

PR 372 (commit `84f9707`, "fix(verify): honor skip_specs in archived-artifact gate") added `scripts/verify-harness.py::skip_specs_declared()` and made the specs check conditional: an archived change whose `.openspec.yaml` declares `skip_specs: true` is exempt from `specs/**/*.md`, and only from that. `tests/test_verify_harness.py::test_archived_change_skip_specs_exempts_specs_only` pins both the exempt and the enforced case.

## Decision

1. The `skip_specs` exemption is the deliberate, narrow exception to ADR-0019 decision 1, scoped to archived changes that declare `skip_specs: true` in their own `.openspec.yaml`.
2. The exemption applies ONLY to the `specs/**/*.md` requirement. Every other required artifact (`proposal.md`, `design.md`, `adr.md`, `tasks.md`, `.openspec.yaml`) stays enforced for that change, and the specs requirement stays enforced for every change that does not declare `skip_specs: true`. `skip_specs` is a declaration of real docs-only scope, never a way to bypass incomplete artifacts.
3. ADR-0019 and ADR-0007 stay accepted and unamended. Accepted ADRs are immutable history, so this exception and its scope are recorded here rather than by editing ADR-0019's Decision section.

## Consequences

A docs-only plan carrier can archive honestly with no spec delta while still carrying the full intent chain. The harness keeps rejecting every change that omits an artifact, so the exemption widens the gate by exactly one declared case.
