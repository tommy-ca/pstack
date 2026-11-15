# Agnix Specification and Design Source Reference

Agnix v0.61.0 specification, configuration, and design source reference.

## Provenance and Ingestion Record

- Raw Source `raw/sources/agnix-agent-config-guard-2026-11-15.md`.
- Ingestion Tool `scripts/llm_wiki.py ingest`.
- Digest `6aa82ed538b3d5c66d2d474873e61747a8145f889d923b7049f9657c64e2b7eb`.
- Scope 327 active files across canonical, host-local, and automation roots.
- Pinned Tool Release [agent-sh/agnix v0.61.0](https://github.com/agent-sh/agnix/releases/tag/v0.61.0).
- Upstream Configuration [Agnix docs](https://github.com/agent-sh/agnix/blob/main/docs/CONFIGURATION.md).

## Classification

- Raw sources are immutable and write-once under `raw/sources/`.
- Curated semantic articles live under `wiki/concepts/` and `wiki/sources/`.
- Navigation indexes are generated projections produced by `scripts/llm_wiki.py index --write`.

## Minimal Semantic Atoms

The atomic blocks are curated in [Agnix Static Guard](../concepts/agnix-agent-guard.md).
The core atoms define the guard interface.
1. `ConfigSource` version-bound file and metadata.
2. `PathDiscovery` detect active skills, agents, rules, and host configurations.
3. `RuleSelector` associate file types, versions, and tool contexts with rules.
4. `Diagnostic` report severity, rule, path, line, and message.
5. `GuardVerdict` validate JSON receipts, exit codes, version, and coverage.
6. `BoundedWitness` falsify gate acceptance logic with finite states and mutant.
7. `HostAdapter` preserve PStack host-specific runtime interfaces.
8. `KnowledgeSource` keep linter findings and provenance independent of authority.

## Verification Boundary

Structural wiki integrity is validated by `scripts/llm_wiki.py check`.
Raw source digests are verified by `scripts/llm_wiki.py verify-sources`.
No live LLM compilation or unexecuted formal proof is claimed.
