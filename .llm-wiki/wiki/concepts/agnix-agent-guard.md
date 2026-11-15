# Agnix Static Guard for PStack Agent Configurations

Agnix v0.61.0 provides cross-tool static lint of Agent Skills, AGENTS.md, agents, and recognized host configurations. This curated article is backed by an observed static lint CI receipt in PR #1409. Ingested raw source provenance is recorded in wiki sources. Live host execution and unbounded formal proof remain unverified.

## Source and scope

- External linter [agent-sh/agnix v0.61.0](https://github.com/agent-sh/agnix/releases/tag/v0.61.0).
- Configuration reference [Agnix documentation](https://github.com/agent-sh/agnix/blob/main/docs/CONFIGURATION.md).
- Proven precedent [QStack Agnix guard](https://github.com/tommy-ca/qstack/blob/main/validate/agnix-config/run.py).
- Native skills baseline [PStack skills](https://github.com/tommy-ca/pstack/tree/main/skills).
- Implementation and acceptance [Epic #1393](https://github.com/tommy-ca/pstack/issues/1393) and [research design doc](https://github.com/tommy-ca/pstack/blob/main/docs/research/agnix-agent-config-guard-2026-11-15.md).
- Ingested source snapshot [Agnix Specification Source Reference](../sources/agnix-specification.md).
- Measured evidence checked 327 files with 0 errors, 37 warnings, and 102 informational diagnostics.

## Minimal semantic atoms

| Atom | Responsibility |
| --- | --- |
| `ConfigSource` | Version-bound file and configuration metadata |
| `PathDiscovery` | Detect active SKILL.md, agents, AGENTS.md, and host rules |
| `RuleSelector` | Associate file types, versions, and tool contexts with rules |
| `Diagnostic` | Report severity, rule ID, path, line, and message |
| `GuardVerdict` | Validate JSON receipts, exit status, version, and coverage |
| `BoundedWitness` | Falsify gate acceptance logic with finite states and mutant |
| `HostAdapter` | Preserve PStack host-specific runtime interfaces |
| `KnowledgeSource` | Keep linter findings and provenance independent of authority |

The design strictly follows core development principles. Domain modeling via `principle-model-the-domain` maps exact Agnix receipt types. Clear containment via `principle-boundary-discipline` prevents arbitrary path traversal and excludes blanket rule suppressions. Incremental progress via `principle-sequence-verifiable-units` orders implementation across five discrete units. Verification tooling via `principle-build-the-lever` builds offline validation scripts. Empirical validation via `principle-prove-it-works` verifies receipts and bounded states.

## Architecture

Data flows from repository files to the reviewed `.agnix.toml` scope. The pinned Agnix CLI processes candidate files and outputs diagnostic JSON receipts. The PStack guard validates receipts against summary counts and policy invariants. Bounded model exploration checks 288 acceptance states with a negative mutant witness. Verified results feed PR evidence and the curated LLM Wiki.

Agnix does not verify real skill invocation, agent dispatch, concurrent isolation, or plugin model behavior. Existing PStack verify skill and formal skill creators remain owners of application journeys and target-specific properties. No generic orchestration runtime is added.

## Findings and gates

PStack's static audit counted 86 skill manifests across canonical, host-local, and automation roots. No extension-recognized helper outside skill-contained `scripts/` directories was found. The guard disallows blanket or active-skill exclusions and rejects a vacuous scan. The 37-warning observed baseline is an enforced ceiling rather than a clean-warnings claim.

Three distinct verification tasks provide proportional proof tiers. Policy verification runs `mise run verify:agnix:policy`. Full static lint runs `mise run verify:agnix`. Bounded model checking runs `mise run verify:agnix:formal`. Raw upstream snapshots are ingested via `scripts/llm_wiki.py ingest` and verified by `scripts/llm_wiki.py verify-sources`.
