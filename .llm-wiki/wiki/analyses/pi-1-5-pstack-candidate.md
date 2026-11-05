# Standalone Pi 1.5.0 → PStack candidate semantic crosswalk

Status: **source-based candidate analysis, NOT live evidence**, 2026-11-05. Parent: [Pi adapter epic #894](https://github.com/tommy-ca/pstack/issues/894).

PStack's canonical workflow intent remains sourced to [Cursor PStack](https://github.com/cursor/plugins/tree/main/pstack), while this port's [17-capability portability specification](https://github.com/tommy-ca/pstack/blob/main/openspec/specs/pstack-portability/spec.md) owns the semantic vocabulary. Pi's separate baseline is [Pi 1.5.0](https://pi.dev/changelog/releases/1.5.0), not the existing OMP adapter.

## Semantic building blocks

- **Native agent loop and context:** Pi owns model interaction, tools, session persistence/resume, context, skill discovery, native MCP, codemode and tool_search.
- **Delegation:** [pi-subagents 0.85.0](https://pi.dev/packages/pi-subagents) may provide agent.spawn, agent.join, agent.cancel, monitor and some steering. It is an optional, separate tool runtime, not Pi core. Independent model families require actual provider/catalog observations.
- **Execution trust:** [pi-better-sandbox 0.14.1](https://pi.dev/packages/pi-better-sandbox) offers independently configured main/subagent/background guards; its fresh switches start OFF. Trusted extension tools are not covered by guarded file rules, and remote SSH effects are outside local confinement.
- **Research:** pi-web-access belongs to researcher/evidence-auditor roles only where needed; never grant broad network rights merely to enable a workflow.
- **PStack workflow semantics:** intent, plan, swarm, arena, interrogate, independent review, acceptance and truth-labelled receipts stay in PStack; no new orchestration engine.
- **Verification:** reuse create-verification-skill, create-formal-verification-skill, and their maintenance loops. Mocked or source-only mappings are static-only and not runtime-verified.
- **Knowledge:** the current Markdown + Git .llm-wiki is the knowledge layer; external docs in this candidate page have **not** yet been captured with scripts/llm_wiki.py ingest. No hash or local raw source claim is made.

## Responsibility crosswalk

| Concern | Pi PStack candidate owner | Design acceptance |
| --- | --- | --- |
| Skill and playbook invocation | Native Pi + canonical PStack skills | No duplicate skill namespaces |
| Agents and multi-model fanout | One pi-subagents engine | Real unique child IDs and resolved models |
| Role and model policy | Host profile/catalog, source-owned roles | No invented model slugs |
| Sandbox and permission | Explicitly enabled guard + OS/container | Denied operations observed and recorded |
| Isolation and integration | Per-writer worktree + host-owned merge | No parent mutation before acceptance |
| Source-backed research | pi-web-access where authorized | External sources recorded with provenance |
| Verification | Existing portable driver and 3-tier evidence | Exact revision and failing negative controls |
| Formal verification | Existing formal skills and installed checker | Bound code relation and failed mutant |
| LLMWiki synthesis | Existing project-local wiki CLI | Sources and runtime claims kept separate |

## Known gaps and resolution

- **No Pi candidate profile, projection, native functional driver, test receipts or local installed-version inventory yet.** These belong to [#895](https://github.com/tommy-ca/pstack/issues/895), [#896](https://github.com/tommy-ca/pstack/issues/896), and [#897](https://github.com/tommy-ca/pstack/issues/897).
- Sandbox/extension interaction, credentials, malicious worktree links and MCP/web admission remain explicitly unproved; see [#897](https://github.com/tommy-ca/pstack/issues/897).
- Formal state invariants and negative mutants remain planned in [#898](https://github.com/tommy-ca/pstack/issues/898).
- Raw source ingestion and hash-backed local sources remain planned in [#899](https://github.com/tommy-ca/pstack/issues/899).
- Actual independent Swarm/Arena/Interrogate and both Thermo-Nuclear reviews remain a gate in [#900](https://github.com/tommy-ca/pstack/issues/900).

See [the full research audit](https://github.com/tommy-ca/pstack/blob/spec/pi-1-5-pstack-adapter-audit/docs/research/pi-1-5-standalone-pstack-audit-2026-11-05.md) for the 17-capability table, supplied 17-extension decisions, trust boundaries and version pins. The six existing shipped harnesses remain the only declared packaged hosts.
