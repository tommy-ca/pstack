# Agnix Static Guard for PStack Agent Configurations

Agnix v0.61.0 provides cross-tool static lint of Agent Skills, AGENTS.md, agents and recognized host rules/configuration. This page is a **curated source-backed design note**, not a completed immutable raw-source ingest, live host run, or unbounded formal proof.

## Source and scope

- External linter: [agent-sh/agnix v0.61.0](https://github.com/agent-sh/agnix/releases/tag/v0.61.0)
- Configuration reference: [Agnix docs](https://github.com/agent-sh/agnix/blob/main/docs/CONFIGURATION.md)
- Proven precedent: [QStack Agnix guard](https://github.com/tommy-ca/qstack/blob/main/validate/agnix-config/run.py)
- Native skills baseline: [PStack skills](https://github.com/tommy-ca/pstack/tree/main/skills)
- Implementation and acceptance: [Epic #1393](https://github.com/tommy-ca/pstack/issues/1393) and [design](../../../docs/research/agnix-agent-config-guard-2026-11-15.md)
- Evidence: source review; live CLI baseline, immutable raw ingestion, verified independent agents **NOT_RUN** unless separate receipts show otherwise.

## Minimal semantic atoms

| Atom | Responsibility |
| --- | --- |
| ConfigSource | Version-bound file and metadata |
| PathDiscovery | Detect active SKILL.md, agents, AGENTS.md and host rules |
| RuleSelector | Associate file types, versions and tool contexts with rules |
| Diagnostic | Report severity, rule, path and location |
| GuardVerdict | Validate JSON/exit/version/coverage and produce scoped result |
| BoundedWitness | Falsify gate-acceptance logic with finite states and mutant |
| HostAdapter | Preserve PStack host-specific runtime interfaces |
| KnowledgeSource | Keep linter findings and provenance independent of authority |

## Architecture

`repository files → .agnix.toml scope → pinned Agnix CLI → diagnostic JSON → PStack guard → static verdict → PR evidence → curated LLMWiki`.

Agnix does not verify real skill invocation, agent dispatch, concurrent isolation, or plugin model behavior. Existing PStack verify skill and formal skill creators remain owners of application journeys and target-specific properties. No generic orchestration runtime is added.

## Findings and gates

PStack's current static audit counted 84 skill manifests; no extension-recognized skill-local helper outside `scripts/` was found. This does not prove the absence of extensionless executables or broken references. The guard disallows blanket or active-skill exclusions and rejects a vacuous scan.

Use `mise run verify:agnix:policy`, `mise run verify:agnix` and `mise run verify:agnix:formal` for distinct evidence tiers. Raw upstream snapshots must be ingested with `scripts/llm_wiki.py ingest` and checked before claiming immutable source capture (tracked #1398).
