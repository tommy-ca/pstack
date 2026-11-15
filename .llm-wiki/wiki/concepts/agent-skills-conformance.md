# Agent Skills: Specification, Semantic Atoms, and PStack Conformance

PStack skill conformance has three independent layers: vendor-neutral Agent Skills metadata, repository-specific layout policy, and observable runtime/formal proof.

## Provenance and scope

- Official Agent Skills specification: https://agentskills.io/specification and https://github.com/agentskills/agentskills/blob/main/docs/specification.mdx
- PStack reference: https://github.com/tommy-ca/pstack/tree/main/skills and https://github.com/tommy-ca/pstack/blob/main/scripts/skill_frontmatter.py
- Canonical upstream: https://github.com/cursor/plugins/tree/main/pstack
- Audit snapshot: 2026-11-15, main tree `2f82965aa0eb6e697446505c5fd696e955756e78`; 84 SKILL.md files total, 67 under canonical skills/, 12 host-local, 5 automation.
- Evidence level: **static/source review only**. No native six-host or independent multi-model verification was performed. This page is curated, **not** an immutable raw-source ingestion or proven semantic compiler run; raw ingestion is tracked by issue #1388.

## Atomic building blocks

| Atom | Inputs | Contract | Output |
| --- | --- | --- | --- |
| Skill identity | Skill directory and SKILL.md | `name` matches directory; kebab-case; length 1–64 | Stable skill ID |
| Activation metadata | YAML frontmatter | Nonblank `description` length 1–1024, says what/when | Discovery trigger |
| Instructions | SKILL.md body | Purpose, steps, failure cases and referenced resources | Agent procedure |
| Executable helper | Optional skill `scripts/` or repository tool | Dependencies, isolation, timeout, exit contract | Reproducible command |
| Reference | Optional `references/`, cross-skill link | Relative path resolves without unintended escape | On-demand context |
| Asset | Optional `assets/` | Exists and has declared usage | Template/data |
| Host binding | Profile + plugin projection | Preserve canonical intent, disclose host gaps | Harness-specific route |
| Structural verifier | Skill files + metadata parser | Reject malformed/omitted fields; do not infer runtime proof | Offline PASS/FAIL |
| Behavioral verifier | Driver + feature map | Launch, doctor, drive, evidence, cleanup | Observed result at revision |
| Formal verifier | Property + code revision + bound | Counterexample or bound-limited proof and failing mutant | Scoped proof evidence |

The Agent Skills specification **allows additional directories**. `scripts/`, `references/`, and `assets/` are conventions; a stricter PStack placement rule must be labeled as a project policy, not as a normative violation.

## Source and execution flow

1. Discover skills across canonical, host-local and automation roots.
2. Parse SKILL.md frontmatter; validate required metadata using a shared contract.
3. Check referenced assets, cross-skill links and optional repository layout policy.
4. Build host-specific projections from the canonical source without duplicating skill intent.
5. Scaffold project-local behavioral/formal verification with distinct proof tiers.
6. Bind verdicts to exact source revision and measured action/side-effect receipts.
7. Curate source-backed semantic atoms in the wiki, index them deterministically and check source provenance.

## Known audit findings

- Shared `verify_skills_frontmatter` formerly checked only name and removed Cursor `mode`, but not description.
- Shared `validate_skill_name` formerly did not enforce the official 64-character maximum.
- Scaffold `check_skill` checked description independently; shared validation is preferred.
- The path inventory found no skill-local `.py`, `.sh`, `.js`, `.ts`, or `.mjs` file outside its own `scripts/`; executable-bit and extensionless checks remain unverified.
- Global `scripts/` is a repository tooling boundary and is not a misplaced skill-specific directory.

## Proven reusable patterns and boundaries

- [Canonical Cursor PStack create-verification-skill](https://github.com/cursor/plugins/blob/main/pstack/skills/create-verification-skill/SKILL.md) defines behavior-first user journey proof. Port the contract via a host adapter; do not reimplement the workflow per host.
- [QStack formal-verify-llmwiki-layout](https://github.com/tommy-ca/qstack/blob/main/.agents/skills/formal-verify-llmwiki-layout/SKILL.md) explicitly distinguishes prior static checks from a source-bound formal proof. PStack should adopt the same claim discipline, not QStack's domain-specific models.
- [QStack verify-governance-hygiene](https://github.com/tommy-ca/qstack/blob/main/.agents/skills/verify-governance-hygiene/SKILL.md) demonstrates typed authority boundaries, negative witnesses, and a GitHub issue graph. Reuse the evidence and planning pattern without transferring quant-specific governance.
- [QStack worktree-protocol](https://github.com/tommy-ca/qstack/blob/main/.agents/skills/worktree-protocol/SKILL.md) keeps executable implementation in skill `scripts/` and detailed docs in `references/`; this is a useful local PStack convention, not an additional mandate of agentskills.io.

## Work graph

Parent: [#1383](https://github.com/tommy-ca/pstack/issues/1383). Shared metadata [#1384](https://github.com/tommy-ca/pstack/issues/1384) precedes complete inventory [#1385](https://github.com/tommy-ca/pstack/issues/1385); path/link policy [#1386](https://github.com/tommy-ca/pstack/issues/1386) and formal proof [#1387](https://github.com/tommy-ca/pstack/issues/1387) feed provenance [#1388](https://github.com/tommy-ca/pstack/issues/1388) and six-host acceptance [#1389](https://github.com/tommy-ca/pstack/issues/1389).

## Verification rule

A structural PASS is not a runtime PASS; a bounded model is not an unbounded proof; a source comparison is not an independent Swarm/Arena/Interrogate run. Reduce evidence conservatively: FAIL > BLOCKED > UNTESTED > PASS, and report scope and source revision.
