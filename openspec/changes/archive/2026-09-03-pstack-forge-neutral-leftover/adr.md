# ADR Review Manifest

- Status: completed
- Review date: 2026-09-03

## Review Summary

ADR review completed for this change. The leftover is a playbook and docs alignment to existing forge-neutral and workflow contracts. It does not change spawn topology, host mapping, version identity, or the Codex compatibility script boundary.

## In-Force ADRs Reviewed

- `adr/0003-benny-grok-is-plugin-installed.md`
- `adr/0004-benny-live-path-is-plugin-skills.md`
- `adr/0005-playbooks-are-not-rhai-workflows.md` — playbooks stay markdown; the Rhai example is docs only.
- `adr/0007-openspec-archive-chain-gate.md`
- `adr/0008-host-adapter-boundary-scope.md` — keep `orch` / `watch-pr` as Codex compatibility; Grok playbooks must not invoke them.
- `adr/0009-semver-grokbuild-not-calver.md`
- `adr/0010-adapter-not-sibling-version.md`
- `adr/0011-single-plugin-repo-not-catalog-folder.md`

## New Durable ADRs Created

- None. No major durable architectural decisions were introduced.
