# ADR Review Manifest

- Status: completed
- Review date: 2026-09-02

## Review Summary

ADR review completed for the manifest lockstep change. The change adds no new durable architectural decision. It applies existing version identity and host-boundary decisions to one additional tracked manifest/index surface. The supersession review confirms ADR-0003 supersedes ADR-0001, ADR-0004 supersedes ADR-0002, and ADR-0008 supersedes ADR-0006.

## In-Force ADRs Reviewed

- `adr/0003-benny-grok-is-plugin-installed.md` — live Grok plugin boundary; no plugin-global hook changes.
- `adr/0004-benny-live-path-is-plugin-skills.md` — host-specific skill paths remain unchanged.
- `adr/0005-playbooks-are-not-rhai-workflows.md` — no workflow or runtime surface changes.
- `adr/0007-openspec-archive-chain-gate.md` — complete intent-driven artifacts remain required.
- `adr/0008-host-adapter-boundary-scope.md` — host path capability differences remain allowed; only version fields are synchronized.
- `adr/0009-semver-grokbuild-not-calver.md` — version remains `MAJOR.MINOR.PATCH-grokbuild.N`.
- `adr/0010-adapter-not-sibling-version.md` — version remains adapter lineage, not catalog sibling identity.
- `adr/0011-single-plugin-repo-not-catalog-folder.md` — pstack remains a single repository with a separate catalog.

## New Durable ADRs Created

- None — no major durable architectural decisions were introduced.
