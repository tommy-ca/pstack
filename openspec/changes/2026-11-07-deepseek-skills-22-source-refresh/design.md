# Design: thin source-to-PStack reusable contract curation

## Primary architecture decision

The correct unit of reuse is a **falsifiable behavior**, not a third-party `SKILL.md`. Source skill titles remain provenance, not installed command names.

```text
pinned external source (read-only, untrusted)
   → 22/22 audit ledger (GENERAL / CONDITIONAL / EXCLUDE)
   → filter: current use? owner? platform relevance? security?
   → existing PStack leaf + principle + playbook mapping
   → actual PStack playbook via poteto-mode
   → host-selected native adapter, authorization and evidence
   → existing exact-head verifier and status reducer
   → QStack adds *only* quant-domain invariants when quant context applies
```

**SOLID:** one concern per owner, rely on capability contracts not DSH concrete tools. **KISS:** keep existing skill names and routing. **DRY:** canonical PStack owner states an invariant once; source ledger only links it. **YAGNI:** add no new leaf, principle, playbook, package, scheduler or serialized type unless a failing test proves the current owner lacks essential behavior.

## Source disposition

See [source-crosswalk.md](source-crosswalk.md) for every pinned source path and existing leaf/principle/playbook mapping:
- **12 GENERAL**: agent-experience, CI test reliability, code review, upgrade guidance, documentation, error handling, simplification, PR description, pre-push validation, prose quality, performance and removal of session-only prose.
- **5 CONDITIONAL**: Agent Notes archiving (when decision records exist), UI/UX, responsive UI, bilingual translation (when a project requires it), browser demo evidence (when a product/user/review workflow requires it). They are not compulsory generic dependencies.
- **5 EXCLUDE**: Cordis lifecycle skill, macOS CUA signing, GitHub-native stack merge implementation, product-specific artwork, DeepSeek session-projection machinery. A generic invariant from an excluded skill may be independently expressed at an existing PStack owner; **its implementation is not imported**.

## Decomposition: what owns what

| Level | Responsibility | Canonical target | Anti-pattern |
| --- | --- | --- | --- |
| Leaf skill | One testable action/report, e.g. a repro or review finding | `fix-ci`, `create-verification-skill`, `interrogate`, both `thermo-nuclear-*`, `benchmark-checklist`, `technical-writing`, `make-pr-easy-to-review` | New `dsh-*` command per upstream file |
| Principle | Cross-workflow invariant (what must remain true) | `principle-prove-it-works`, `principle-subtract-before-you-add`, `principle-boundary-discipline`, `principle-guard-the-context-window`, `principle-experience-first`, `principle-separate-before-serializing-shared-state` | Duplicated rules in each source adaptation |
| Playbook | Order and termination of engineering work | Existing `bug-fix`, `investigation`, `refactoring`, `perf-issue`, `opening-a-pr`, `shipping`, `visual-parity`, `authoring-a-skill` | New giant DSH orchestrator |
| Host adapter | Actually supported commands, identity and permissions | Active PStack `profiles/<host>.json` + tool refs | Hardcoded pnpm, Cordis, gh stack, CUA |
| Project/domain overlay | Nonportable constraints and domain invariants | Target project, QStack quant-only when applicable | Vendor features generalized into PStack |
| Evidence | Exact execution state and target receipt | Existing 4-plane, 3-tier verifier | Source claims promoted to runtime PASS |

Existing semantic blocks B01–B20 already live in [the archived first audit](../archive/2026-10-11-deepseek-skill-portability/atomic-patterns.md). Do not mint 20 new classes or another registry. Two domain-independent refinements worth testing are **resource ownership through asynchronous shutdown** and **PR claims tied to exact executed evidence**.

## Code and data flows

**Review:** `intent/scope → investigation or review playbook → exact base/head → read source and consumers → Thermos correctness/quality passes → reproducible finding or explicit UNTESTED → existing evidence`.

**Bug / flaky CI:** `bug-fix/fix-ci → acquire isolated test resource → wait for observable readiness → deterministic overlap barrier → negative control → bounded teardown until quiescence → current-head receipt`. A fixed sleep is not a readiness proof; a caught exception is not rollback.

**Refactor:** `refactoring → consumer reachability → maintained obligations → smaller design → behavior parity and negative control → approved diff`. Deleted LOC alone is not a quality metric.

**Docs / PR:** `technical-writing → user-visible contract and migration → commands actually observed → exact-head test results → report gaps`. No project-independent AI-use percentages, mandated GUI GIFs, translation structure, or release paths.

**Quant:** `PStack development playbook → QStack capability overlay and domain verifier → quant receipts by reference`; never PStack calls QStack or qorch manages generic software work.

## Minimal conceptual records

These are **documentation fields**, not a new serialized runtime schema:

```yaml
SourceDisposition:
  source: {repository: deepseek-ai/deepseek-harness, commit: git-sha, path: skill-path, license: MIT}
  classification: GENERAL | CONDITIONAL | EXCLUDE
  reason: why the rule transfers or is excluded
  owner: existing PStack skill/principle/playbook, or none
  verified: SOURCE_STATIC
RetainedBehavior:
  trigger: positive task condition
  negative_trigger: excluded context/capability
  preconditions: [invariant]
  postconditions: [observable outcome]
  forbidden_shortcuts: [vendor assumption or unsafe omission]
  covering_test: existing gate identifier or UNTESTED
```

**No independent `VerificationReceipt` model.** Refer to existing serialized PStack evidence: canonical/adapter/package/runtime planes; actual host and code SHA; `FAIL > BLOCKED > UNTESTED > PASS`. `SKIP` means irrelevant, not `PASS`. A changed head invalidates stale behavioral evidence.

## Review operators (available only when actually executed)

- **Swarm:** partition source areas into CI/review, agent-context/docs, frontend and domain-specific exclusions. Every independent worker receives the *same immutable source pin*, a narrow slice, explicit negative triggers and a report shape. No shared write operations.
- **Arena:** compare distinct architectures only if a genuinely unresolved structural decision remains, using a predeclared rubric: safety, owner alignment, maintenance overhead, testability, host portability, and negative-trigger correctness. An accepted proposal is not an Arena victory unless at least two isolated candidates were actually evaluated.
- **Interrogate:** adversarially search real source/diff for false claims, swallowed partial mutations, lifecycle races, scope escape, invalid test selection, and exclusions that accidentally activate. Retain only defects reproduced by an actual command/test; source-only risk is NOT_RUN/UNTESTED, not a verified finding.

## Release gates and negative cases

| Probe | Expected behavior |
| --- | --- |
| Backend-only review | No UI capture, bilingual workflow, artwork or signing |
| GitHub stack CLI absent | Shipping reports adapter gap; never silently assumes `gh stack` |
| Resource cleanup races with callback | Deterministic probe identifies unsafe last-use ordering |
| False green stale-head result | No current-head PASS |
| Partial transaction + automatic retry | Recovery owner must establish safe continuation |
| Source mentions `pnpm` or a credential path | No automatic execution/access |
| Source-only readers claim Swarm/Arena/Interrogate PASS | Claim rejected as unexecuted |
| An existing PStack skill already fulfills rule | No extra leaf/principle/playbook created |

## Unimplemented scope
No PStack skill bodies, model routing, host projection packages, runtime adapters or QStack code change in this specification-only branch. Source drift warrants review; it is not proof of missing runtime functionality.
