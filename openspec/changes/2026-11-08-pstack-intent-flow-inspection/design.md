# Design: host-neutral intent-driven change inspection and fail-closed validation

## Context

- Template: [intent-driven-template@b5bda460](https://github.com/intent-driven-dev/intent-driven-template/tree/b5bda460a2180a55fc508fdedc4ef058d95355db), whose brownfield installer explicitly requires reviewing and preserving pre-existing config rather than blindly replacing it.
- PStack already has `openspec/config.yaml`, a **locally extended** `openspec/schemas/intent-driven` with five templates, many living capability specs, archived changes, and `scripts/openspec_change.py`.
- Accepted architecture decisions: `adr/0007-openspec-archive-chain-gate.md`, `adr/0019-post-archive-completeness.md`, `adr/0020-skip-specs-exception-to-post-archive-completeness.md`. Preserve each immutable record; skip-specs does not erase any other gate.
- PStack has six established host adapters, `pstack.package.json` role truth, and portable verification receipts; OpenSpec is a design-time layer, not another agent orchestration runtime.

## Goals / Non-Goals

**Goals:** simple source-visible active-change status with explicit provenance, strict separate schema validation, mise entry points, CI regression checks, and one up-to-date lifecycle document.

**Non-goals:** copying template `.opencode` role/agent package, installing Superpowers, adding a new workflow runtime, modifying accepted ADRs, guessing host or model results, rewriting archived source history, or adding another schema catalog.

## Components and code/data flow

```text
                  openspec/config.yaml (intent-driven)
                                  |
                  openspec/schemas/intent-driven/
                                  |
                     active changes/* folders
                                  |
             scripts/openspec_change.py (existing owner)
                /                              \
  --status [--json] [--change]           verify [--change]
          |                                    |
   inspect_intent_chain          check artifact chain
          |                                    |
   Path inspection only                 subprocess: openspec schema
          |                             validate intent-driven
   typed JSON artifact state                    |
   task progress + missing                  subprocess: openspec
          |                              validate <change> --strict
  mise openspec:status                            |
       filesystem-only                      PASS/FAIL/BLOCKED
          \                                     /
           `docs/verification-test-tiers.md` separates evidence
```

- Input: direct child directory under `openspec/changes/` (excluding `archive` and hidden archives), .openspec.yaml, the five standard artifacts, task checkboxes. Symlinked artifacts and unsafe change names are rejected at the filesystem boundary. No repository file is changed by inspection.
- Output: JSON object with `schema`, `stage_order`, `inspection_level`, `changes[]` and `summary`. Each change includes `artifacts` (five bools), `schema`, `skip_specs`, `specs_exempt`, `missing[]`, `next_stage`, `planning_chain_ready`, `tasks` (`total`, `done`, `status`), `evidence`.
- Status does **not** report "implemented", "validated" or "archived" from file presence. Strict validation uses OpenSpec subprocess and returns nonzero on CLI errors or artifact gaps; zero exit only after actual CLI validation.
- Existing `resolve_openspec_change` and `validate_openspec_change` retain old tuple-compatible and single-active change semantics for downstream callers; the new status/verify modes extend the existing CLI rather than replacing it.
- The new offline inventory is explicitly a separate operation from the merged `--status` wrapper (which uses actual `openspec status` and may be ambiguous when multiple changes are active). The shell/CLI is thin: pure, deterministic file scanner for offline tests; external OpenSpec at a single subprocess boundary; no global state, service, persistence, or host import.

## Data schema (contract shape)

```json
{
  "schema": "intent-driven",
  "stage_order": ["proposal", "specs", "design", "adr", "tasks"],
  "inspection_level": "filesystem-only; not OpenSpec validation",
  "summary": {"total": 1, "planning_ready": 1, "incomplete": 0},
  "changes": [{
    "name": "sample-change",
    "schema": "intent-driven",
    "skip_specs": false,
    "artifacts": {"proposal": true, "specs": true, "design": true, "adr": true, "tasks": true},
    "specs_exempt": false,
    "missing": [],
    "next_stage": null,
    "planning_chain_ready": true,
    "tasks": {"total": 3, "done": 0, "status": "in-progress"},
    "evidence": "filesystem-only; OpenSpec CLI and execution unverified"
  }]
}
```

This is illustrative serialization, **not** a claimed schema-validated or observed result. No new persistent receipt registry or parallel schema is introduced.

## Decisions / Alternatives

1. **Extend `openspec_change.py`.** Reuse its existing OpenSpec boundary and test module (#761/#762). Reject a second OpenSpec CLI wrapper or Node-based state tracker (DRY/KISS).
2. **Inspect from direct filesystem.** Allows a non-destructive status view when OpenSpec is absent. Reject inference from `openspec list --json` for artifact completeness, since that CLI can be unavailable or use task status rather than all five files.
3. **Keep strict verification external.** Run actual schema/change OpenSpec commands; no local regex or JSON schema scan may claim strict spec correctness.
4. **Retain local schema.** PStack's already-vendored schema is richer than the template's copy; import only missing workflow configuration and instructions. No unrequested installation of OpenCode agents, dependencies, or user-global config.
5. **Preserve archives and accepted ADRs.** Maintain pre-archive, archived completeness and skip-specs exceptions separately; status never archives or rewrites.

## Risks / Trade-offs

- **Pre-existing changes are partially drafted:** global verify will fail until accepted planning artifacts are complete; named `--change` permits targeted verification.
- **OpenSpec binary missing:** status still runs, strict verify returns BLOCKED nonzero, and CI records OpenSpec CLI NOT_RUN.
- **One-off symlink or malicious path:** boundary validates names and rejects symlinked files/directories.
- **Checkbox completion can be mistaken for implementation:** JSON and docs clearly label it task-text progress only.
- **Template version drift:** template commit is linked, local schema stays authoritative until a separate compatibility audit.

## Migration / Rollback

First merge the source-only inspector, tests, config and spec on a draft PR. Run PStack offline CI and scaffold gates at its exact head. Explicitly run OpenSpec CLI later in a prepared development environment. Merge only after independent review of changed diff. A rollback removes this change's additional inspector/mise/config sections; do not overwrite the pre-existing schema, host adapters, accepted ADRs or historical archives.

## Open Questions

The exact OpenSpec CLI version to pin under `mise` requires compatibility testing against existing local schema and all active changes. Do not add a guessed version to PStack's toolchain. A future optional `spec-as-source` BDD layer would be a separate capability proposal, not part of this minimal setup.
