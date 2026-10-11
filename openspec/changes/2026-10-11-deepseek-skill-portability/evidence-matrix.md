# Source-to-pstack adoption ledger

All source URLs below are pinned under [DeepSeek Harness @ d7432673](https://github.com/deepseek-ai/deepseek-harness/tree/d743267388641bc76f17c45ce8b4c231aed1d32c/.agents/skills). “Source documented” means present in a source skill, **not** independently replicated, scientifically proven superior, or verified on pstack.

| Source skill | Extracted transferable invariant | pstack owner / intended mapping | Decision |
|---|---|---|---|
| `agent-experience` | Minimal initial context, discoverable deferred resources, bounded outputs, constraints before side effects, measure total work | `principle-guard-the-context-window`; skill-authoring playbook; host tool descriptions | **Refine P1** |
| `dsh-archive-agent-notes` | Classify keep/delete/archive by future decision value, preserve provenance, immutable archived records | `technical-writing`, `reflect`, optional documentation/knowledge pack | **Optional P2**, not generic archival format |
| `dsh-ci-test-reliability` | Atomic resource allocation, state-based readiness, global restoration, quiescent cleanup, negative-control races | `create-verification-skill`, `maintain-verification-skill`, `fix-ci` | **Pilot P0** |
| `dsh-client-ui-ux` | Reuse tokens/components, feedback surface, overlay/window safety, test light/dark/viewport | `visual-parity`, `feature` optional UI profile | **Optional P2**, exclude DSH styling literals |
| `dsh-code-review` | Read exact live base/head, inspect complete scope and consumers, prioritize correctness/security/lifecycle over nits | `thermo-nuclear-code-quality-review`, `interrogate`, `babysit` | **Refine P1** |
| `dsh-create-upgrade-guide` | Publish migration steps alongside externally observable breaking changes | `feature`, `technical-writing`, optional releases | **Optional P2**, exclude DSH paths |
| `dsh-doc` | Audience-first docs, authoritative facts, verify executed behavior, one owner per truth | `technical-writing`, docs owner | **Refine P2**, multilingual pairs optional |
| `dsh-error-handling` | Typed failure identity, effect uncertainty, recovery owner, visible safe next action | `bug-fix`, `interrogate`, `principle-boundary-discipline` | **Refine P1** |
| `dsh-find-simplifications` | Delete maintained obligations; prove consumer reachability and net reduction without semantic change | `refactoring`, `principle-subtract-before-you-add`, `thermo-nuclear-code-quality-review` | **Refine P1** |
| `dsh-merging-stacked-prs` | Base/head discipline, stack preflight, native stack semantics when available | `shipping`, `babysit`, forge adapter | **Defer** mandatory `gh stack`; feature-detect |
| `dsh-pre-push-checks` | Change-scope gate selection, verify exact target/head, rerun only invalidated evidence | `fix-ci`, `babysit`, verification driver | **Pilot P0** |
| `dsh-prose-standard` | Preserve propositions/obligations while removing redundancy; code comments explain non-obvious rules | `technical-writing`, `unslop`, skill authoring | **Refine P1** |
| `dsh-speed-up-perf` | Realistic workload baseline, user-path measurements, preserve behavior, no speculative speedups | `perf-issue`, `hillclimb`, `benchmark-checklist` | **Optional P1**, avoid duplicate perf skill |
| `dsh-translate-docs` | Explicit invocation, minimal counterpart updates, authoritative source per change | `technical-writing` optional i18n playbook | **Optional P2**; do not auto-trigger |
| `dsh-trim-cot-leakage` | Remove session-only residue; restate durable, verifiable repository facts; preserve valid citations | `technical-writing`, `unslop` | **Refine P1** as provenance hygiene, no request for private reasoning |
| `record-browser-gif` | Same-commit real run and isolated browser capture; differentiate demo from production proof | `show-me-your-work`, `visual-parity` optional GUI artifact | **Optional P2**, do not require credentials/GIF on every project |

## Crosswalk priorities

**Wave 0 (prove first):** `dsh-ci-test-reliability` + `dsh-pre-push-checks`. Exact-head review and typed failures form the next controlled pilot. Documentation, perf, UI and i18n are conditional domain behaviors, not ambient policy.

**Existing ownership prevails:** all refinements MUST be merged at the canonical skill/playbook/principle owner; avoid `dsh-*` additions to the common `skills/` inventory unless #310 demonstrates a unique repeatable decision and no existing owner.

**Evidence ladder:** source-documented → pstack-baseline observed → candidate regression observed → native-host observed. Each step has its own revision-tied artifacts; none implies the next. For serialized portability receipts use existing schema and tier vocabulary, not new enum names.

## Source artifacts beyond the sixteen SKILL.md files

References exist under `dsh-ci-test-reliability`, `dsh-doc`, `dsh-find-simplifications`, `dsh-prose-standard`, `dsh-trim-cot-leakage`, and an encoder and unittest under `record-browser-gif/scripts/`. These supply rationale and optional fixture ideas; they are **not** evidence that pstack has executed those tests. Exact content mapping and acceptance ledger belong to #308.
