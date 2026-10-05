# Portable package descriptor and deterministic harness projection

- Status: Accepted
- Date: 2026-10-05
- Deciders: Architecture Gate (Issue #79, Arena and Interrogate Synthesis)

## Context

Harness adapters (Grok Build, Codex, OMP, OpenCode) require configuration files to discover skills and lifecycle hooks. Maintaining separate manifests manually across four harnesses introduces drift. Monolithic configuration embedding runtime orchestration violates RFC 2119 separation invariants defined in Unit 3.

## Decision

Adopt the Arena Candidate 1 architecture with Candidate 2 native schema grafts:

1. Maintain one canonical root package descriptor `pstack.package.json`. It conforms strictly to `schemas/portability/package-descriptor.schema.json`.
2. Prohibit runtime orchestration fields inside package descriptors.
3. Build a deterministic projection lever `scripts/project-package.py`. The lever projects `pstack.package.json` into harness native configurations:
   - `.grok-plugin/plugin.json` for Grok Build.
   - `.codex-plugin/plugin.json` for Codex.
   - `.omp-plugin/plugin.json` for Oh-My-Pi.
   - `.opencode-plugin/package.json` for OpenCode.
4. Gate manifest synchronization in CI via `scripts/project-package.py --check` inside `scripts/verify-portable.py doctor`.

## Consequences

- Package metadata has a single authoritative source of truth.
- Adding a fifth harness requires updating `pstack.package.json` and extending `scripts/project-package.py`.
- Native harnesses consume idiomatic manifest formats with zero runtime middleware.
- Manifest drift across harnesses is prevented by automated doctor checks.
