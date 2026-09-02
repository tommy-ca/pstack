# ADR Review Manifest

- Status: completed
- Review date: 2026-09-02

## Review Summary

This change adds a narrow archive-task outcome convention. It does not change plugin topology, host orchestration, version identity, or release architecture. Existing archive and host-boundary decisions remain applicable.

## In-Force ADRs Reviewed

- `adr/0003-benny-grok-is-plugin-installed.md` — no Benny packaging change.
- `adr/0004-benny-live-path-is-plugin-skills.md` — no Benny path change.
- `adr/0005-playbooks-are-not-rhai-workflows.md` — no playbook runtime change.
- `adr/0007-openspec-archive-chain-gate.md` — archive artifact gates remain in force.
- `adr/0008-host-adapter-boundary-scope.md` — sibling marketplace and installed-host mutations remain outside this adapter change.
- `adr/0009-semver-grokbuild-not-calver.md` — no version grammar change.
- `adr/0010-adapter-not-sibling-version.md` — no adapter identity change.
- `adr/0011-single-plugin-repo-not-catalog-folder.md` — the sibling marketplace remains a separate repository.

ADR-0001 is superseded by ADR-0003, ADR-0002 is superseded by ADR-0004, and ADR-0006 is superseded by ADR-0008; those files were reviewed for the supersession graph and are not in force.

## New Durable ADRs Created

- None — the outcome annotation is a spec-level archive convention, not a major architectural decision.
