# ADR Review Manifest

- Status: completed
- Review date: 2026-09-05

## Review Summary

The change preserves the existing adapter boundary. It adds executable and plan-validation contracts but does not introduce a new durable architecture, storage system, forge, host runtime, or release policy. No repository-level ADR is created or modified.

The supersession graph reviewed was `ADR-0003 -> ADR-0001`, `ADR-0004 -> ADR-0002`, and `ADR-0008 -> ADR-0006`. ADR-0008 remains marked `Proposed`; its boundary wording is covered by the existing `pstack-grok-host-boundary` specification and is intentionally not rewritten here.

## In-Force ADRs Reviewed

- `adr/0003-benny-grok-is-plugin-installed.md`
- `adr/0004-benny-live-path-is-plugin-skills.md`
- `adr/0005-playbooks-are-not-rhai-workflows.md`
- `adr/0007-openspec-archive-chain-gate.md`
- `adr/0008-host-adapter-boundary-scope.md` (boundary wording; status metadata remains Proposed)
- `adr/0009-semver-grokbuild-not-calver.md`
- `adr/0010-adapter-not-sibling-version.md`
- `adr/0011-single-plugin-repo-not-catalog-folder.md`

Superseded and retained as history: `ADR-0001`, `ADR-0002`, and `ADR-0006`.

## New Durable ADRs Created

- None - no major durable architectural decisions were introduced.
