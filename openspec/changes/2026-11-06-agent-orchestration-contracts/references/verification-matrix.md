# Agent orchestration verification and formal falsification matrix

**Status:** SPECIFIED / NOT RUN. This is a design matrix for existing PStack verification skill generators, not a claimed live result. Parent epic [#916](https://github.com/tommy-ca/pstack/issues/916), verification issue [#919](https://github.com/tommy-ca/pstack/issues/919).

Use existing `skills/create-verification-skill/SKILL.md` to generate a *project-local* `verify-<app>` skill for an actual installed adapter, and `skills/create-formal-verification-skill/SKILL.md` to model its real critical state transitions. Use `maintain-formal-verification-skill` whenever code mapped by a formal model changes. These are extension requirements, not duplicate new generator skills.

## Negative-control scenarios

| ID | Effect under test | Intentionally failing mutant / trigger | Required observation | Tier |
| --- | --- | --- | --- | --- |
| V-AO-01 | Request idempotency | Retry identical ID with changed branch | Explicit conflict; 0 additional launches | native/live |
| V-AO-02 | Unknown startup | Drop response after launch but before receipt | Observe unresolved; no duplicate launch | native/live |
| V-AO-03 | Observation purity | Change observe to dispatch on missing record | Mutant caught; observe has no side effects | offline + live |
| V-AO-04 | Terminal identity | Substitute receipt from another execution or SHA | FAIL/UNTESTED; cannot satisfy parent gate | offline |
| V-AO-05 | Cancel fence | Deliver success callback after accepted cancellation | Parent never PASS; result retained only as history | model + live |
| V-AO-06 | Child custody | Parent announces done with unresolved child | Close rejected or BLOCKED; child retained | native/live |
| V-AO-07 | Dirty worktree | Create untracked file and simulate orphan cleanup | No deletion absent verified preservation | native/live |
| V-AO-08 | Lost host | Drop host observation while child is in flight | Unknown/lost, not done; no silent retry | model + live |
| V-AO-09 | Swarm coverage | One of N required slices times out | Gap remains, aggregate not blanket PASS | offline |
| V-AO-10 | Arena independence | Reuse same warm child context across candidates | Degraded independence reported, not N independent seats | offline |
| V-AO-11 | Interrogate falsifier | Reviewer returns speculative bug without runnable repro | Finding dropped/BLOCKED, not confirmed | offline |
| V-AO-12 | Wrong evidence tier | No installed executor, static docs check passes | Static may PASS; live BLOCKED or UNTESTED | offline |
| V-AO-13 | Capability denial | Missing spawn permission; test fallback via TTY injection | Fail-closed, no child launched | native/live |
| V-AO-14 | Graph scope | PStack DevTask marked done from qorch research unit | Refuse wrong policy authority | offline |

## Reproducible verification hierarchy

1. **Tier 1 (static/offline):** Validate schema, source pin, dependency graph cycle rejection, version, required IDs, receipt/acceptance binding, verdict reduction, and mockable negative controls. Use the repository's existing validation/pytest harness; do not invent a successful command invocation.
2. **Tier 2 (native smoke):** Detect the active harness and verify real worker spawn/observe/join/cancel/authorization with an isolated checkout and bounded deadline. If tools absent, report `BLOCKED` rather than synthetic PASS.
3. **Tier 3 (observed live):** Drive the actual app/CLI from a fresh instance or isolated worktree, capture terminal output, child ID, exact Git revision, affected file data, clean recovery and teardown. A success transcript without a proven state transition is insufficient.
4. **Formal layer (if an implementation requires it):** Model exactly the atomic code operations implementing `prepare`, `launch`, `observe`, `cancel`, `settle`, `release`; choose TLA+/TLC for races. Use code-level bounded properties or property testing for purely functional reducer/validator behavior. Absence of Java/TLC = `BLOCKED`, no borrowed proofs.

## Minimal formal model outline

Inputs: 2 parent invocations, 2 worker incarnations, 2 attempts per invocation, 1 capacity slot, finite reordered events and 1 host loss. Model with exact code-matched transition labels *after* the actual adapter code exists.

**Safety S1 — AtMostOneLaunch:** for each owner+request binding, count of real launch effects <= 1 unless a new request ID and explicit new intent was recorded.

**Safety S2 — TerminalProof:** `accepted(task)` implies `terminalProof.executionId == task.executionId`, `evidence.revision == task.revision`, and all required checks PASS.

**Safety S3 — CancelFence:** `cancelled(execution)` excludes accepted completion, even if a delayed callback arrives.

**Safety S4 — NoUnsafeCleanup:** a worktree with dirty/untracked changes cannot be destroyed unless a verified retained recovery artifact exists.

**Safety S5 — OwnerCustody:** while a child is open, the parent remains incomplete or carries a verified transfer receipt.

**Conditional liveness L1 — BoundedProgress:** if an admitted agent can run, its host can respond, and a fair scheduler eventually executes enabled steps, the parent eventually observes completion, a blocker, or timeout. State each fairness assumption; unresponsive hosts invalidate this liveness precondition.

### Mutation bars (must be demonstrated in target code)

- Remove the idempotency compare-and-set guard: S1 fails with two launches.
- Reorder receipt validation and PASS transition: S2 fails with wrong-execution proof.
- Remove cancel-epoch check: S3 fails after a late callback.
- Skip the dirty/untracked check: S4 fails with lost work.
- Drop owner-child closure guard: S5 fails while a child remains live.

A proof without an observed reachable mutant is **DRAFT**. A borrowed upstream model or unspecified atomicity is not a PStack formal pass. Link checks to target function names, exact commit, version of model checker, bounds and counterexample sequence. Keep safety separate from conditional liveness.

## Review and acceptance gates

- **Swarm:** independent slices `source/schema`, `lifecycle/retries`, `authorization/worktree`, `evidence/verification`. Require actual separate workers for an executed swarm. Coordinator-only inspection is not a swarm run.
- **Arena:** compare `native-host-only`, `one opt-in adapter`, `generic multi-backend protocol`; frozen rubric: correctness, accidental complexity, independent testability, minimal migration, rollback. Prefer the smallest evidence-backed design.
- **Interrogate:** adversaries try to violate S1-S5; each finding survives only after a lead reruns a bounded reproduction.
- **Thermos:** [code quality](https://github.com/cursor/plugins/blob/2776ddd2355d6d6c8747d3964600f28daf62f049/thermos/skills/thermo-nuclear-code-quality-review/SKILL.md) checks giant modules, conditional growth, indirection, and layer ownership; [correctness/security](https://github.com/cursor/plugins/blob/2776ddd2355d6d6c8747d3964600f28daf62f049/thermos/skills/thermo-nuclear-review/SKILL.md) reviews the changed diff, not hypothetical upstream bugs.
- **Receipt:** report base SHA, changed paths, commands/exits, negative-mutant result, actual host/worker IDs, evidence level, skipped lanes, and scope. If no execution occurs, report `NOT_RUN`.

## Decision gate

No production adapter should be accepted until V-AO-01..08, V-AO-12..13, and S1-S5 have target-linked, runnable negative controls; weaker scope must be explicitly marked BLOCKED/UNTESTED. A pure contract/doc proposal may proceed as a draft with this limitation visible.
