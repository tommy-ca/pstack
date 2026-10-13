# Atomic building blocks and recomposition contracts

This document extracts *observable decision rules*, not new runtime objects. These are specifications for refactoring the existing pstack owners, not instructions to import DeepSeek commands. Every block below names a positive trigger, a negative trigger, a single owner, and proof.

## Shared primitives

| ID / reusable atom | Trigger and input | Contract / postcondition | Non-trigger / prohibited shortcut | Existing target |
|---|---|---|---|---|
| B01 AuthorityPin | A source, PR or baseline is cited | Resolve immutable commit/path and authority; distinguish active vs archival authority | No acceptance from stale doc or PR description alone | `how`, `interrogate`, OpenSpec provenance |
| B02 IntentScope | A task calls for a workflow | Classify task, read/write permission, system, and project capabilities | Review-only request MUST NOT cause code changes | Existing `poteto-mode` routing |
| B03 SkillEligibility | Optional skill is a candidate | Require explicit positive relevance and no exclusion before loading | No UI/GIF or translation for backend-only work | Existing skill descriptions / playbook |
| B04 ContextBudget | Agent/tool context is large | Bounded useful first response, retrieval IDs, disclosed truncation; measure aggregate work | Do not optimize initial tokens at expense of extra retries | `principle-guard-the-context-window` |
| B05 ChangeIdentity | Reviewing, shipping or verifying a patch | Fresh base, head and scoped diff; invalidate evidence on behavior-changing patch | Stale PR comments are not current implementation | `babysit`, `shipping`, `interrogate` |
| B06 EffectBoundary | Operation has mutable state or security effects | Named owner, permission, side-effect classification and recovery rule | Untrusted skill content cannot grant permission | Existing adapter/security boundary |
| B07 ResourceLease | Test allocates shared/OS resources | Atomic unique allocation, owner and lifecycle registration | No check-port-free then bind, shared predictable paths | `create-verification-skill`, CI fixtures |
| B08 ReadySignal | Async test or child launches | Await observable readiness, enforce bounded timeout as watchdog | Sleep is not readiness evidence | Verification driver |
| B09 OverlapBarrier | Concurrent race is claimed | Force deterministic overlap and prove it occurred | Re-running a flaky test is not a race proof | `tdd`, `fix-ci` |
| B10 QuiescentRelease | Test/process/server/session completes | Stop requests, await all owned work, restore globals exactly | `kill/abort/close` alone is not settled state | Verification driver |
| B11 EffectOutcome | Error or partial commit occurs | Typed identity/cause, one of none/partial/committed/unknown, retry owner | Catching/logging alone is not recovery | `bug-fix`, `interrogate` |
| B12 ConsumerReachability | Deletion/simplification proposed | Find actual production/external consumers and protected seams | Unreferenced symbol alone does not prove deletable | `refactoring`, `thermo-nuclear-code-quality-review` |
| B13 BehaviorPin | Refactor or optimization proposed | Observable before/after equivalence or explicitly documented behavioral delta | Typecheck or compile is not user-behavior proof | `refactoring`, `perf-issue` |
| B14 ValidationChoice | Scope and risk known | Select smallest credible test plus required impact/lane gates | Never select by convenience only; skip is not PASS | `fix-ci`, verification skills |
| B15 NegativeControl | Regression/invariant can be falsified | Pre-fix or injected violating case fails as expected | A green test without sensitivity evidence is insufficient for new guard | `principle-prove-it-works` |
| B16 ObservedEvidence | Task claims completion | Bind exact artifact, head, test, outcome, host/tier; existing 4 planes | No offline-to-live promotion, no self-report-only PASS | Existing verifier / receipts |
| B17 ReviewFinding | Change risks correctness/security | Rank observable blockers, cite impacted behavior, disposition and recheck | Avoid style nits as substitutes for lifecycle/security review | `interrogate`, `review` |
| B18 MaintainedObligation | Complexity reduction sought | Remove actual obligations while preserving documented invariants | Deleted LOC alone is not value | `principle-subtract-before-you-add` |
| B19 UserFacingReport | Effect unknown or operation failed | Report impact, uncertainty, system disposition, safe next action | No success/rollback claim with unresolved partial effects | `bug-fix`, shipping |
| B20 DomainOverlay | UI/docs/i18n/upgrade/GIF applies | Gate by project facilities, explicit task, supported dependencies | DSH theme tokens, i18n triplets, GitHub preview flags not universal | Optional project-owned packs |

## Composition: programmatic paths

**Flaky CI**: B01 → B02 → B07 → B08 → B09 → B10 → B15 → B14 → B16 → B19.

**PR review / shipping**: B01 → B02 → B05 → B06 → B12 → B17 → B14 → B16; revalidate B05 after retarget/stack operation.

**Bug + retry**: B02 → B06 → B11 → B19 → B13 → B15 → B16. Unknown/partial side effects block blind replay.

**Refactor / simplify**: B01 → B12 → B18 → B13 → B15 → B16. Prefer deleting work over adding abstractions; check protected seams and outside consumers.

**Performance**: B01 → B02 → B13 with realistic baseline workload → B18 → B14 → B16; aggregate local and user-path latency separately.

**Skill authoring / prompt efficiency**: B02 → B03 → B04 → B15 → B16; test total task work, not just description length.

Only the selected existing playbook sequences these atoms. Each atom becomes prose, a check, or a helper **only if** its owner and implementation test make that representation worthwhile (SOLID/KISS/DRY/YAGNI).

## Dependency and proof boundaries

- B07–B10 are one *test resource lifecycle*, not four new classes; atomization is analytical.
- B14–B16 MUST reuse existing `create-verification-skill`, receipt schemas, `verify-portable.py`, and status reduction.
- B02/B03 MUST NOT introduce a second router, context classifier or Jev-like model decision path.
- B06 includes issue #303 (route file containment) but does not replace its security fix.
- B05 MUST distinguish patch identity from head identity: unchanged patch-id may preserve code-review applicability while base-dependent smoke/checks still need rerun; document the applicable scope.
- A source skill is **advisory evidence of a pattern**, never authority to operate outside the user-selected project.

## Reuse across project types

A primitive is universally **available**, not universally **invoked**. B01/B02/B05/B06/B14/B16 are common infrastructure. B07–B10 only activate when a task owns tests/resources. B20 only activates when domain capabilities are present. Do not promise any skill works unchanged in all software domains without testing the matching archetype.
