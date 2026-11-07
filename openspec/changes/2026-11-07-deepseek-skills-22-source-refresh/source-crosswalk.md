# Curated DeepSeek source classification → canonical PStack owners

**Pinned DeepSeek source:** `deepseek-ai/deepseek-harness@fcc0ad462172522aaf5c93a7b2e01f6b9f0b0159` (MIT). **Evidence:** SOURCE_STATIC, GitHub repository inspection; no native host execution or independent model panel. Previous baseline: `d743267388641bc76f17c45ce8b4c231aed1d32c` (16 source skills).

**Disposition:** 12 GENERAL + 5 CONDITIONAL + 5 EXCLUDE = 22. These are source classifications, **not** 17 new installed skills. **Zero DSH-specific skills are imported into PStack**. Every retained contract maps to an existing leaf skill, principle and PStack playbook; all source paths remain listed only for provenance.

## Classification rules

- **GENERAL**: relevant to multiple engineering project types; rewrite only the behavior, not source names, commands, CI/layout/PR templates or platform prerequisites. Incorporate only when an owner-specific negative test shows a missing behavior.
- **CONDITIONAL**: reusable guidance for a legitimate task family (UI, language pairing, ADR archiving, browser evidence); requires actual user/task applicability and a target-project policy/host capability; absence is SKIP, not BLOCKED.
- **EXCLUDE**: implementation is coupled to DSH/Cordis, a single platform/product, or a non-general subsystem. Do not register the source skill or add its runtime requirements to the general PStack specification. An independently general invariant may be stated once by an already-owned PStack contract.

## Full 22/22 provenance and decomposition

| Pinned source `SKILL.md` | Class | Reusable contract or exclusion | Existing PStack leaf skill | Existing principle | Existing playbook |
| --- | --- | --- | --- | --- | --- |
| [`agent-experience`](https://github.com/deepseek-ai/deepseek-harness/blob/fcc0ad462172522aaf5c93a7b2e01f6b9f0b0159/.agents/skills/agent-experience/SKILL.md) | **GENERAL** | Context-efficient discoverable tool contracts | technical-writing | principle-guard-the-context-window | authoring-a-skill |
| [`cordis-styling-nitpicking`](https://github.com/deepseek-ai/deepseek-harness/blob/fcc0ad462172522aaf5c93a7b2e01f6b9f0b0159/.agents/skills/cordis-styling-nitpicking/SKILL.md) | **EXCLUDE** | Cordis-specific lifecycle audit; distill generic cleanup invariants only | — | — | — |
| [`dsh-archive-agent-notes`](https://github.com/deepseek-ai/deepseek-harness/blob/fcc0ad462172522aaf5c93a7b2e01f6b9f0b0159/.agents/skills/dsh-archive-agent-notes/SKILL.md) | **CONDITIONAL** | Decision record retention by future value; no DSH archive triplets | reflect | principle-encode-lessons-in-structure | investigation |
| [`dsh-ci-test-reliability`](https://github.com/deepseek-ai/deepseek-harness/blob/fcc0ad462172522aaf5c93a7b2e01f6b9f0b0159/.agents/skills/dsh-ci-test-reliability/SKILL.md) | **GENERAL** | Atomic fixture allocation, observable readiness, quiescent teardown and negative controls | create-verification-skill, fix-ci | principle-separate-before-serializing-shared-state | bug-fix |
| [`dsh-client-ui-ux`](https://github.com/deepseek-ai/deepseek-harness/blob/fcc0ad462172522aaf5c93a7b2e01f6b9f0b0159/.agents/skills/dsh-client-ui-ux/SKILL.md) | **CONDITIONAL** | Inspect relevant rendered states and real interaction paths; no DSH style tokens | create-verification-skill | principle-experience-first | visual-parity |
| [`dsh-code-review`](https://github.com/deepseek-ai/deepseek-harness/blob/fcc0ad462172522aaf5c93a7b2e01f6b9f0b0159/.agents/skills/dsh-code-review/SKILL.md) | **GENERAL** | Exact-head semantic review of lifecycles, consumers, interfaces and regressions | thermo-nuclear-review, interrogate | principle-prove-it-works | investigation |
| [`dsh-create-upgrade-guide`](https://github.com/deepseek-ai/deepseek-harness/blob/fcc0ad462172522aaf5c93a7b2e01f6b9f0b0159/.agents/skills/dsh-create-upgrade-guide/SKILL.md) | **GENERAL** | Actionable migration only when external behavior or persistence changes | technical-writing | principle-migrate-callers-then-delete-legacy-apis | shipping |
| [`dsh-cua-macos-signing`](https://github.com/deepseek-ai/deepseek-harness/blob/fcc0ad462172522aaf5c93a7b2e01f6b9f0b0159/.agents/skills/dsh-cua-macos-signing/SKILL.md) | **EXCLUDE** | Mac-specific CUA keychain/certificate and permission steps; not shared engineering | — | — | — |
| [`dsh-doc`](https://github.com/deepseek-ai/deepseek-harness/blob/fcc0ad462172522aaf5c93a7b2e01f6b9f0b0159/.agents/skills/dsh-doc/SKILL.md) | **GENERAL** | Audience-first documentation, executable claims, one owner per fact | technical-writing | principle-minimize-reader-load | feature |
| [`dsh-error-handling`](https://github.com/deepseek-ai/deepseek-harness/blob/fcc0ad462172522aaf5c93a7b2e01f6b9f0b0159/.agents/skills/dsh-error-handling/SKILL.md) | **GENERAL** | Typed failure identity, effect status, recovery owner and safe action | interrogate, fix-ci | principle-boundary-discipline | bug-fix |
| [`dsh-find-simplifications`](https://github.com/deepseek-ai/deepseek-harness/blob/fcc0ad462172522aaf5c93a7b2e01f6b9f0b0159/.agents/skills/dsh-find-simplifications/SKILL.md) | **GENERAL** | Prove maintained obligations removed without losing consumer behavior | thermo-nuclear-code-quality-review | principle-subtract-before-you-add | refactoring |
| [`dsh-merging-stacked-prs`](https://github.com/deepseek-ai/deepseek-harness/blob/fcc0ad462172522aaf5c93a7b2e01f6b9f0b0159/.agents/skills/dsh-merging-stacked-prs/SKILL.md) | **EXCLUDE** | Official GitHub gh stack mechanics excluded; PR dependency integrity stays in shipping | — | — | — |
| [`dsh-official-plugin-artwork`](https://github.com/deepseek-ai/deepseek-harness/blob/fcc0ad462172522aaf5c93a7b2e01f6b9f0b0159/.agents/skills/dsh-official-plugin-artwork/SKILL.md) | **EXCLUDE** | Product-specific icons, brand palette, export dimensions and approval rules | — | — | — |
| [`dsh-pr-description`](https://github.com/deepseek-ai/deepseek-harness/blob/fcc0ad462172522aaf5c93a7b2e01f6b9f0b0159/.agents/skills/dsh-pr-description/SKILL.md) | **GENERAL** | PR motivation, observable change, tests actually run and evidence gaps; no DSH template | make-pr-easy-to-review | principle-prove-it-works | opening-a-pr |
| [`dsh-pre-push-checks`](https://github.com/deepseek-ai/deepseek-harness/blob/fcc0ad462172522aaf5c93a7b2e01f6b9f0b0159/.agents/skills/dsh-pre-push-checks/SKILL.md) | **GENERAL** | Diff-scoped targeted checks and exact-head result invalidation | fix-ci, create-verification-skill | principle-prove-it-works | shipping |
| [`dsh-prose-standard`](https://github.com/deepseek-ai/deepseek-harness/blob/fcc0ad462172522aaf5c93a7b2e01f6b9f0b0159/.agents/skills/dsh-prose-standard/SKILL.md) | **GENERAL** | Preserve complete contracts in prose; eliminate duplication and review narration | technical-writing | principle-minimize-reader-load | feature |
| [`dsh-responsive-ui`](https://github.com/deepseek-ai/deepseek-harness/blob/fcc0ad462172522aaf5c93a7b2e01f6b9f0b0159/.agents/skills/dsh-responsive-ui/SKILL.md) | **CONDITIONAL** | Verify responsive content, focus, action reachability and touch/hover when UI exists | create-verification-skill | principle-experience-first | visual-parity |
| [`dsh-session-projection`](https://github.com/deepseek-ai/deepseek-harness/blob/fcc0ad462172522aaf5c93a7b2e01f6b9f0b0159/.agents/skills/dsh-session-projection/SKILL.md) | **EXCLUDE** | DSH-specific projection contract; event-sourcing verification belongs in project domains | — | — | — |
| [`dsh-speed-up-perf`](https://github.com/deepseek-ai/deepseek-harness/blob/fcc0ad462172522aaf5c93a7b2e01f6b9f0b0159/.agents/skills/dsh-speed-up-perf/SKILL.md) | **GENERAL** | Representative user-path benchmark, reproducible baseline and behavior parity | benchmark-checklist | principle-explain-the-number | perf-issue |
| [`dsh-translate-docs`](https://github.com/deepseek-ai/deepseek-harness/blob/fcc0ad462172522aaf5c93a7b2e01f6b9f0b0159/.agents/skills/dsh-translate-docs/SKILL.md) | **CONDITIONAL** | Minimal counterpart updates only under project translation policy | technical-writing | principle-minimize-reader-load | feature |
| [`dsh-trim-cot-leakage`](https://github.com/deepseek-ai/deepseek-harness/blob/fcc0ad462172522aaf5c93a7b2e01f6b9f0b0159/.agents/skills/dsh-trim-cot-leakage/SKILL.md) | **GENERAL** | Remove session-only prose and unverifiable rationale while retaining durable facts | unslop, technical-writing | principle-minimize-reader-load | refactoring |
| [`record-browser-gif`](https://github.com/deepseek-ai/deepseek-harness/blob/fcc0ad462172522aaf5c93a7b2e01f6b9f0b0159/.agents/skills/record-browser-gif/SKILL.md) | **CONDITIONAL** | Truthful visual evidence only when requested or required; no compulsory GIF/keys | create-verification-skill | principle-prove-it-works | visual-parity |

## Leaf, principle and playbook decomposition

**Leaf skills (atomic operation / observable outcome):** use installed `create-verification-skill`, `fix-ci`, `interrogate`, `thermo-nuclear-review`, `thermo-nuclear-code-quality-review`, `benchmark-checklist`, `make-pr-easy-to-review`, `technical-writing`, `unslop`, `reflect`. Do not create a DSH namespace; a source skill is not automatically an independent leaf.

**Principles (cross-task invariants, no execution authority):** reuse `principle-prove-it-works`, `principle-subtract-before-you-add`, `principle-boundary-discipline`, `principle-separate-before-serializing-shared-state`, `principle-guard-the-context-window`, `principle-experience-first`, `principle-minimize-reader-load`, `principle-migrate-callers-then-delete-legacy-apis`, `principle-encode-lessons-in-structure`, `principle-explain-the-number`.

**Playbooks (sequencing, not duplicated rule bodies):** retain PStack `authoring-a-skill`, `bug-fix`, `investigation`, `feature`, `refactoring`, `perf-issue`, `opening-a-pr`, `shipping` and `visual-parity`. `poteto-mode` remains the sole general entry/router; Swarm/Arena/Interrogate are already-existing situational skills, not new cross-cutting playbooks.

## Exclusion decisions and salvage boundaries

1. **Cordis:** omit plugin-entrypoint mechanics, P0 singleton severity and Cordis-specific disposal APIs. Keep the generic idea that acquired effects need explicit owners and quiescent teardown, in existing review/formal verification.
2. **macOS signing:** omit certificate creation, private keychain paths, auto-recommendation, and local permission procedures entirely. The active host adapter owns any security-sensitive setup, subject to explicit authorization.
3. **GitHub native stacks:** omit `gh stack` enforcement and merge semantics as a universal capability. PStack shipping can verify actual PR dependency order and select its supported forge adapter; never fall back to an unsafe merge silently.
4. **Artwork:** omit DSH icon language, 36×36 SVG dimensions, brand styling and mandatory approval procedures; project-specific design rules stay in the product repository.
5. **Session projections:** omit DSH `SessionProjection` definitions and runtime wiring. Event-sourced projects may apply established generic replay/test principles via their project-specific formal verifier, without activating a general PStack projection skill.

## Additional DSH-specific exclusions within retained sources

- No `pnpm --silent run change-scope`, Cordis registry, package paths or private DSH architecture conventions as PStack generic commands.
- No Chinese/English mandatory paired docs, release-specific upgrade-guide directory, AI Usage scoring rubric, DSH-native PR title structure or mandatory live-API GIF.
- No automatic choice of macOS signing, model credentials, GitHub native stack extension, network settings, secret paths or user-local state changes.
- No new generalized capability enum, skill graph, task scheduler, receipt reducer or copied source text. MIT provenance remains with source links; substantial copying requires license attribution.

## Adoption threshold / SOLID, KISS, DRY, YAGNI

Before editing a current leaf, trace the actual consumer and verify that the original owner fails a focused behavioral regression. Add the smallest invariant to that owner and its test, then rerun exact-head validation. If an existing skill already satisfies the invariant, **adopt by reference only**. Add a new leaf **only** for a recurring, independently invoked operation with a distinct testable output and no existing owner. Add a principle only for a truly cross-workflow invariant not covered upstream. Add a playbook only for new repeatable sequencing not already in `poteto-mode`. This source audit authorizes none of those new artifacts by itself.
