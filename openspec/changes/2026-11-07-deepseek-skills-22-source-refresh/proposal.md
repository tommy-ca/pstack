# Proposal: curate general developer-agent contracts from DeepSeek's 22 skills

## Intent
Reconcile the existing PStack DeepSeek portability specification with a newer, immutable upstream skill inventory. **Keep only generally reusable engineering behavior in PStack**, retain conditional guidance only for tasks that need it, and **exclude source-specific implementations**. The existing PStack skills, principles, playbooks, host adapters and verifier remain canonical.

## Why
The archived October 2026 audit classified sixteen skills at `d7432673`. The inspected DeepSeek Harness `master` at `fcc0ad462172522aaf5c93a7b2e01f6b9f0b0159` contains twenty-two SKILL.md directories: six new and eight previously existing directories with modified tree IDs. Its terminology, runtime, docs layout, Cordis system and native tooling must **not** silently become PStack requirements.

## What changes
- **Source-ledger completeness:** classify all 22 (12 GENERAL / 5 CONDITIONAL / 5 EXCLUDE), including a traceable exclusion rationale. Keep the original 16-skill archived decisions intact.
- **Taxonomy:** map each retained behavior to an **existing leaf skill**, cross-workflow **principle** and PStack **playbook**. No wholesale import, vendor namespace, second router, extra proof reducer or speculative new skill.
- **Formal requirements:** replace overly broad 22-skill activation requirements with a minimal portable filter, resource-lifecycle semantic verification and PR migration/evidence truth.
- **Evaluation:** define Swarm source-coverage, Arena design comparison and Interrogate executable falsification as **later gates**. They have not run in this spec-only change.

## Source probes (SOURCE_STATIC, read-only)
- `GET https://api.github.com/repos/deepseek-ai/deepseek-harness/contents/.agents/skills?ref=fcc0ad462172522aaf5c93a7b2e01f6b9f0b0159` — 22 directories.
- `GET https://api.github.com/repos/deepseek-ai/deepseek-harness/contents/.agents/skills?ref=d743267388641bc76f17c45ce8b4c231aed1d32c` — 16 directories.
- `tommy-ca/pstack/openspec/specs/pstack-reusable-skill-patterns/spec.md` — canonical current spec, originally sixteen-source formulation.
- `tommy-ca/pstack/skills/` and `skills/poteto-mode/playbooks/` — owner and playbook inventories.
- DeepSeek repository license: MIT. Retain source links/commit attribution; source instructions are lower-trust evidence.

## Boundaries
PStack owns generic engineering orchestration. QStack invokes PStack through `qstack-mode → poteto-mode` and adds quant-only invariants without cloning general skills. Thermos reviews remain installed canonical PStack/host skills and are not re-imported as DSH copies. DSH-specific Cordis, signing, graphics, native-stack and Session projection machinery **cannot** activate through this proposal.

## Acceptance
A consistent 22/22 source ledger with exclusions, a minimal complete OpenSpec delta, unchanged existing runtime skill count, and explicit NOT_RUN follow-up gates. This proposal does not declare source-to-target functional improvement, live multi-host conformance, or executable multi-model review.

## Recursive execution graph
The live [issue-graph.md](issue-graph.md) records [#1060](https://github.com/tommy-ca/pstack/issues/1060) and its four minimal leaf gates: [#1061](https://github.com/tommy-ca/pstack/issues/1061) source/spec review → ([#1062](https://github.com/tommy-ca/pstack/issues/1062) lifecycle/review ∥ [#1063](https://github.com/tommy-ca/pstack/issues/1063) optionality/non-trigger) → [#1064](https://github.com/tommy-ca/pstack/issues/1064) independent acceptance. Old #305–#315 remain closed. Existing #1054/#1058 own verification tools and host CI. No source skill maps directly to an issue; a new implementation task requires a real failing test.
