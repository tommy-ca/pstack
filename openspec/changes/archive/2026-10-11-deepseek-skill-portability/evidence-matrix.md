# Source-to-pstack adoption ledger

All source URLs below are pinned under [DeepSeek Harness @ d7432673](https://github.com/deepseek-ai/deepseek-harness/tree/d743267388641bc76f17c45ce8b4c231aed1d32c/.agents/skills). “Source documented” means present in a source skill, **not** independently replicated, scientifically proven superior, or verified on pstack.

| Source skill | Extracted transferable invariant | pstack owner / intended mapping | Decision |
|---|---|---|---|
| [`agent-experience`](https://github.com/deepseek-ai/deepseek-harness/blob/d743267388641bc76f17c45ce8b4c231aed1d32c/.agents/skills/agent-experience/SKILL.md) | Minimal initial context, discoverable deferred resources, bounded outputs, constraints before side effects, measure total work | `principle-guard-the-context-window`; skill-authoring playbook; host tool descriptions | **Refine P1** |
| [`dsh-archive-agent-notes`](https://github.com/deepseek-ai/deepseek-harness/blob/d743267388641bc76f17c45ce8b4c231aed1d32c/.agents/skills/dsh-archive-agent-notes/SKILL.md) | Classify keep/delete/archive by future decision value, preserve provenance, immutable archived records | `technical-writing`, `reflect`, optional documentation/knowledge pack | **Optional P2**, not generic archival format |
| [`dsh-ci-test-reliability`](https://github.com/deepseek-ai/deepseek-harness/blob/d743267388641bc76f17c45ce8b4c231aed1d32c/.agents/skills/dsh-ci-test-reliability/SKILL.md) | Atomic resource allocation, state-based readiness, global restoration, quiescent cleanup, negative-control races | `create-verification-skill`, `maintain-verification-skill`, `fix-ci` | **Pilot P0** |
| [`dsh-client-ui-ux`](https://github.com/deepseek-ai/deepseek-harness/blob/d743267388641bc76f17c45ce8b4c231aed1d32c/.agents/skills/dsh-client-ui-ux/SKILL.md) | Reuse tokens/components, feedback surface, overlay/window safety, test light/dark/viewport | `visual-parity`, `feature` optional UI profile | **Optional P2**, exclude DSH styling literals |
| [`dsh-code-review`](https://github.com/deepseek-ai/deepseek-harness/blob/d743267388641bc76f17c45ce8b4c231aed1d32c/.agents/skills/dsh-code-review/SKILL.md) | Read exact live base/head, inspect complete scope and consumers, prioritize correctness/security/lifecycle over nits | `thermo-nuclear-code-quality-review`, `interrogate`, `babysit` | **Refine P1** |
| [`dsh-create-upgrade-guide`](https://github.com/deepseek-ai/deepseek-harness/blob/d743267388641bc76f17c45ce8b4c231aed1d32c/.agents/skills/dsh-create-upgrade-guide/SKILL.md) | Publish migration steps alongside externally observable breaking changes | `feature`, `technical-writing`, optional releases | **Optional P2**, exclude DSH paths |
| [`dsh-doc`](https://github.com/deepseek-ai/deepseek-harness/blob/d743267388641bc76f17c45ce8b4c231aed1d32c/.agents/skills/dsh-doc/SKILL.md) | Audience-first docs, authoritative facts, verify executed behavior, one owner per truth | `technical-writing`, docs owner | **Refine P2**, multilingual pairs optional |
| [`dsh-error-handling`](https://github.com/deepseek-ai/deepseek-harness/blob/d743267388641bc76f17c45ce8b4c231aed1d32c/.agents/skills/dsh-error-handling/SKILL.md) | Typed failure identity, effect uncertainty, recovery owner, visible safe next action | `bug-fix`, `interrogate`, `principle-boundary-discipline` | **Refine P1** |
| [`dsh-find-simplifications`](https://github.com/deepseek-ai/deepseek-harness/blob/d743267388641bc76f17c45ce8b4c231aed1d32c/.agents/skills/dsh-find-simplifications/SKILL.md) | Delete maintained obligations; prove consumer reachability and net reduction without semantic change | `refactoring`, `principle-subtract-before-you-add`, `thermo-nuclear-code-quality-review` | **Refine P1** |
| [`dsh-merging-stacked-prs`](https://github.com/deepseek-ai/deepseek-harness/blob/d743267388641bc76f17c45ce8b4c231aed1d32c/.agents/skills/dsh-merging-stacked-prs/SKILL.md) | Base/head discipline, stack preflight, native stack semantics when available | `shipping`, `babysit`, forge adapter | **Defer** mandatory `gh stack`; feature-detect |
| [`dsh-pre-push-checks`](https://github.com/deepseek-ai/deepseek-harness/blob/d743267388641bc76f17c45ce8b4c231aed1d32c/.agents/skills/dsh-pre-push-checks/SKILL.md) | Change-scope gate selection, verify exact target/head, rerun only invalidated evidence | `fix-ci`, `babysit`, verification driver | **Pilot P0** |
| [`dsh-prose-standard`](https://github.com/deepseek-ai/deepseek-harness/blob/d743267388641bc76f17c45ce8b4c231aed1d32c/.agents/skills/dsh-prose-standard/SKILL.md) | Preserve propositions/obligations while removing redundancy; code comments explain non-obvious rules | `technical-writing`, `unslop`, skill authoring | **Refine P1** |
| [`dsh-speed-up-perf`](https://github.com/deepseek-ai/deepseek-harness/blob/d743267388641bc76f17c45ce8b4c231aed1d32c/.agents/skills/dsh-speed-up-perf/SKILL.md) | Realistic workload baseline, user-path measurements, preserve behavior, no speculative speedups | `perf-issue`, `hillclimb`, `benchmark-checklist` | **Optional P1**, avoid duplicate perf skill |
| [`dsh-translate-docs`](https://github.com/deepseek-ai/deepseek-harness/blob/d743267388641bc76f17c45ce8b4c231aed1d32c/.agents/skills/dsh-translate-docs/SKILL.md) | Explicit invocation, minimal counterpart updates, authoritative source per change | `technical-writing` optional i18n playbook | **Optional P2**; do not auto-trigger |
| [`dsh-trim-cot-leakage`](https://github.com/deepseek-ai/deepseek-harness/blob/d743267388641bc76f17c45ce8b4c231aed1d32c/.agents/skills/dsh-trim-cot-leakage/SKILL.md) | Remove session-only residue; restate durable, verifiable repository facts; preserve valid citations | `technical-writing`, `unslop` | **Refine P1** as provenance hygiene, no request for private reasoning |
| [`record-browser-gif`](https://github.com/deepseek-ai/deepseek-harness/blob/d743267388641bc76f17c45ce8b4c231aed1d32c/.agents/skills/record-browser-gif/SKILL.md) | Same-commit real run and isolated browser capture; differentiate demo from production proof | `show-me-your-work`, `visual-parity` optional GUI artifact | **Optional P2**, do not require credentials/GIF on every project |

## Crosswalk priorities

**Wave 0 (prove first):** `dsh-ci-test-reliability` + `dsh-pre-push-checks`. Exact-head review and typed failures form the next controlled pilot. Documentation, perf, UI and i18n are conditional domain behaviors, not ambient policy.

**Existing ownership prevails:** all refinements MUST be merged at the canonical skill/playbook/principle owner; avoid `dsh-*` additions to the common `skills/` inventory unless #310 demonstrates a unique repeatable decision and no existing owner.

**Evidence ladder:** source-documented → pstack-baseline observed → candidate regression observed → native-host observed. Each step has its own revision-tied artifacts; none implies the next. For serialized portability receipts use existing schema and tier vocabulary, not new enum names.

## Source artifacts beyond the sixteen SKILL.md files

References exist under `dsh-ci-test-reliability`, `dsh-doc`, `dsh-find-simplifications`, `dsh-prose-standard`, `dsh-trim-cot-leakage`, and an encoder and unittest under `record-browser-gif/scripts/`. These supply rationale and optional fixture ideas; they are **not** evidence that pstack has executed those tests. Exact content mapping and acceptance ledger belong to #308.

## Source-audit strength and qualification status

The source repository is MIT licensed. Each matrix row above links to its pinned `SKILL.md` source at a frozen repository commit; content is advisory material, not trusted execution policy. Current evidence for all sixteen skills is **source documented** only with respect to transfer into pstack. The source tree also contains ancillary references and `record-browser-gif/scripts/test_encode_gif.py`, but that is only an encoder test, not proof of universally correct GUI demos or cross-host effectiveness.

**Most defensible near-term reuse** is the behavior whose failures are externally falsifiable:
- `dsh-ci-test-reliability`: per-resource atomic allocation, state readiness, controlled overlap, lifecycle settlement (E01/E02).
- `dsh-pre-push-checks`: exact changed scope, bounded gate selection, head revision checks (E03).
- `dsh-code-review`: actual patch plus consumers and lifecycle, not PR narrative (E03/E05).
- `dsh-error-handling`: typed identity, partial/unknown effect handling, recovery authority (E04).
- `dsh-find-simplifications`: consumer reachability, maintained-obligation reduction, equivalence (E05).

The remaining skills are either already represented in pstack (`agent-experience`, `dsh-prose-standard`, `dsh-speed-up-perf`), narrowly conditional (`dsh-doc`, UI, archives, i18n, upgrade, GIF), or tied to contingent tooling (`dsh-merging-stacked-prs`). They are not rejected as ideas; importing their entire text would create redundant or inappropriate global policy.

Per-skill triggers, source-path links, execution negatives, data models, and claim stages are governed by [atomic-patterns.md](atomic-patterns.md) and [qualification-and-eval.md](qualification-and-eval.md). The dedicated [qualification schema](schemas/skill-pattern-qualification.schema.json) can be used by issue #308 to structure source-specific records. Exact future source inventory MUST be rediscovered from its pin and not hardcoded as a permanent universal count.
