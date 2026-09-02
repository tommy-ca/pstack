# ADR Review Manifest

- Status: completed
- Review date: 2026-09-02

## Review Summary

The refresh ports upstream behavior and metadata into an existing host-adapter boundary. It does not introduce a new durable architecture decision or change version grammar, plugin topology, orchestration ownership, or playbook storage.

## In-Force ADRs Reviewed

- `adr/0003-benny-grok-is-plugin-installed.md` — live Benny remains plugin-installed without global hooks.
- `adr/0004-benny-live-path-is-plugin-skills.md` — live Benny paths and upstream reference split remain unchanged.
- `adr/0005-playbooks-are-not-rhai-workflows.md` — playbooks remain markdown skills, not Rhai workflows.
- `adr/0007-openspec-archive-chain-gate.md` — design and ADR artifacts remain required before archive.
- `adr/0008-host-adapter-boundary-scope.md` — Grok host boundaries and Codex-only compatibility utilities remain distinct.
- `adr/0009-semver-grokbuild-not-calver.md` — versions retain `MAJOR.MINOR.PATCH-grokbuild.N`.
- `adr/0010-adapter-not-sibling-version.md` — versions do not adopt `-pstack.N`.
- `adr/0011-single-plugin-repo-not-catalog-folder.md` — pstack remains a single-plugin repository.

ADR-0001 is superseded by ADR-0003, ADR-0002 is superseded by ADR-0004, and ADR-0006 is superseded by ADR-0008; those files were reviewed for the supersession graph and are not in force.

## New Durable ADRs Created

- None — no major durable architectural decisions were introduced.
